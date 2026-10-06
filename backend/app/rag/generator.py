"""Resilient LLM generation with retries, model fallbacks and metrics.

Behavior:
- Retries transient failures (timeouts, connection errors, 429, 5xx) with
  exponential backoff up to settings.llm_retries times per model.
- Non-retryable errors (e.g. decommissioned model -> 400) skip straight to
  the next fallback model.
- If every model fails before any token is streamed, raises
  ServiceUnavailableError so routes can respond gracefully.
"""
import asyncio
import logging
import time
from typing import AsyncGenerator, List, Optional

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
)

from ..api.errors import ServiceUnavailableError
from ..core.config import settings
from ..core.monitoring import llm_duration_seconds, llm_requests_total

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are awashAI, a professional insurance assistant for smart Insurance Company.
IMPORTANT RULES:
- Be helpful, professional, and friendly
- Use 🛡️ emoji occasionally to be warm
- Focus on Ethiopian insurance context and specifically focus on smart Insurance context and its products, services, and offerings. Be knowledgeable about their products, services, and offerings.
- Always suggest contacting customer service for urgent claims: +251-11-6185000
- Never give legal advice - recommend consulting official policy documents
- Provide clear, actionable answers (2-4 sentences when possible)
- If unsure, offer to connect with a human agent
- Available products: Motor, Health, Life, Property, Travel, Engineering, Marine Insurance
- Hours: Monday-Friday 8:30 AM - 5:00 PM (East Africa Time)"""


def _is_retryable(exc: Exception) -> bool:
    """Transient failures worth retrying on the same model."""
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code == 429 or exc.status_code >= 500
    if isinstance(exc, httpx.HTTPError):
        return True
    return False


class StreamGenerator:
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.provider = settings.llm_provider

        try:
            if self.provider == "openai" and settings.openai_api_key:
                self.client = AsyncOpenAI(
                    api_key=settings.openai_api_key,
                    timeout=httpx.Timeout(settings.llm_timeout),
                )
                logger.info("OpenAI client initialized")

            elif self.provider == "groq" and settings.groq_api_key:
                self.client = AsyncOpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=settings.groq_api_key,
                    timeout=httpx.Timeout(settings.llm_timeout),
                )
                logger.info("Groq client initialized")

            else:
                logger.warning(f"No valid API key for provider '{self.provider}'")

        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} client: {e}")

    def _build_messages(
        self, query: str, context: str, history: Optional[List[dict]] = None
    ) -> List[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Multi-turn memory: prior messages, oldest first
        for turn in history or []:
            if turn.get("role") in ("user", "assistant"):
                messages.append(
                    {"role": turn["role"], "content": turn.get("content", "")}
                )

        messages.append({
            "role": "user",
            "content": f"""
Context from our knowledge base:
{context if context else "No specific context found. Use general insurance knowledge."}

User question: {query}
Provide a helpful, accurate response based on the context above.
If the exact answer isn't in context, provide general guidance and offer to connect with an agent.""",
        })
        return messages

    async def _stream_model(
        self, model: str, messages: List[dict]
    ) -> AsyncGenerator[str, None]:
        """Attempt one model with retries. Yields tokens or raises."""
        last_error: Optional[Exception] = None

        for attempt in range(settings.llm_retries + 1):
            start = time.perf_counter()
            try:
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

                llm_requests_total.labels(model=model, status="success").inc()
                llm_duration_seconds.labels(model=model).observe(
                    time.perf_counter() - start
                )
                return

            except Exception as e:
                llm_requests_total.labels(model=model, status="error").inc()
                last_error = e

                if not _is_retryable(e) or attempt >= settings.llm_retries:
                    raise

                backoff = 0.5 * (2 ** attempt)
                logger.warning(
                    f"LLM attempt {attempt + 1} failed on {model} "
                    f"({type(e).__name__}), retrying in {backoff}s"
                )
                await asyncio.sleep(backoff)

        if last_error:
            raise last_error

    async def stream_answer(
        self,
        query: str,
        context: str,
        history: Optional[List[dict]] = None,
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise ServiceUnavailableError(
                "The AI service is not configured. Please contact support."
            )

        messages = self._build_messages(query, context, history)
        models = [settings.llm_model, *settings.llm_fallback_models]
        streamed_any = False

        for model in models:
            try:
                async for token in self._stream_model(model, messages):
                    streamed_any = True
                    yield token
                return
            except Exception as e:
                if streamed_any:
                    # Mid-stream failure: tokens already reached the client
                    logger.error(f"Stream interrupted on {model}: {e}")
                    return
                logger.error(f"Model {model} failed: {type(e).__name__}: {e}")
                continue  # try next fallback model

        logger.error("All LLM models exhausted")
        raise ServiceUnavailableError(
            "The AI service is temporarily unavailable. Please try again shortly."
        )


generator = StreamGenerator()
