"""v1 API routes: chat (sync + SSE), health, history, feedback, catalog."""
import json
import logging
import uuid
from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ...core.config import settings
from ...core.monitoring import chat_messages_total
from ...core.security import verify_api_key
from ...rag.generator import generator
from ...rag.retriever import retriever
from ...services.database import db_manager
from ...services.monitoring import system_monitor
from ...services.quote_engine import FLOWS, calculate_quote
from ..errors import AppException, ServiceUnavailableError
from .schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    HealthResponse,
    HistoryResponse,
    InsuranceType,
    QuoteFlowResponse,
    QuoteRequest,
    QuoteResponse,
    QuoteStartRequest,
    ReadinessResponse,
    Source,
)

router = APIRouter()
logger = logging.getLogger(__name__)

FALLBACK_ANSWER = (
    "⚠️ I'm experiencing technical difficulties. Please contact our support "
    "team at +251-11-6185000 for immediate assistance."
)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """Non-streaming chat with retrieval, memory and persistence."""
    session_id = request.session_id or uuid.uuid4().hex

    history = await db_manager.get_history(session_id, settings.memory_window)
    result = await retriever.get_result(request.message)

    chunks: List[str] = []
    try:
        async for chunk in generator.stream_answer(
            request.message, result.context, history
        ):
            chunks.append(chunk)
        answer = "".join(chunks)
    except ServiceUnavailableError as e:
        logger.error(f"Chat unavailable: {e.detail}")
        answer = FALLBACK_ANSWER
    except AppException:
        raise

    await db_manager.save_conversation(
        session_id, request.message, answer, request.metadata
    )
    chat_messages_total.labels(role="user").inc()
    chat_messages_total.labels(role="assistant").inc()

    return ChatResponse(
        answer=answer,
        session_id=session_id,
        sources=[Source(**s) for s in result.sources[:3]],
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """Streaming chat over Server-Sent Events."""
    session_id = request.session_id or uuid.uuid4().hex

    async def event_generator() -> AsyncGenerator[str, None]:
        chunks: List[str] = []
        try:
            history = await db_manager.get_history(session_id, settings.memory_window)
            result = await retriever.get_result(request.message)

            yield _sse({"type": "start", "session_id": session_id})
            yield _sse({"type": "sources", "sources": result.sources[:3]})

            async for chunk in generator.stream_answer(
                request.message, result.context, history
            ):
                chunks.append(chunk)
                yield _sse({"type": "token", "content": chunk})

            yield _sse({"type": "end"})

            if chunks:
                await db_manager.save_conversation(
                    session_id, request.message, "".join(chunks), request.metadata
                )
                chat_messages_total.labels(role="user").inc()
                chat_messages_total.labels(role="assistant").inc()

        except ServiceUnavailableError as e:
            logger.error(f"Stream unavailable: {e.detail}")
            yield _sse({"type": "error", "error": FALLBACK_ANSWER})
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield _sse({"type": "error", "error": "Unexpected error. Please retry."})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health", response_model=HealthResponse)
async def health():
    """Shallow liveness probe (no dependency checks)."""
    return HealthResponse(status="healthy", service="awash-ai-backend")


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness():
    """Deep readiness probe covering vector store, LLM and database."""
    from ...rag.vector_store import vector_store

    components = {
        "vector_store": vector_store.vector_store is not None,
        "llm_client": generator.client is not None,
        "database": await db_manager.is_ready(),
    }
    overall = "ready" if all(components.values()) else "degraded"
    return ReadinessResponse(
        status=overall, components=components, system=system_monitor.status()
    )


@router.get("/conversations/{session_id}/history", response_model=HistoryResponse)
async def conversation_history(
    session_id: str, api_key: str = Depends(verify_api_key)
):
    messages = await db_manager.get_history(session_id, limit=100)
    return HistoryResponse(session_id=session_id, messages=messages)


@router.get("/insurance-types", response_model=List[InsuranceType])
async def get_insurance_types(api_key: str = Depends(verify_api_key)):
    return [
        {"id": "motor", "name": "Motor Insurance", "icon": "🚗", "description": "Protect your vehicle"},
        {"id": "health", "name": "Health Insurance", "icon": "🏥", "description": "Medical coverage"},
        {"id": "life", "name": "Life Insurance", "icon": "❤️", "description": "Family protection"},
        {"id": "property", "name": "Property Insurance", "icon": "🏠", "description": "Home & assets"},
        {"id": "travel", "name": "Travel Insurance", "icon": "✈️", "description": "Trip protection"},
        {"id": "business", "name": "Business Insurance", "icon": "💼", "description": "Commercial coverage"},
    ]


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest, api_key: str = Depends(verify_api_key)
):
    """Persist user feedback for continuous improvement."""
    saved = await db_manager.save_feedback(
        feedback.session_id, feedback.rating, feedback.comment
    )
    if not saved:
        logger.warning("Feedback received but persistence is unavailable")
    logger.info(f"Feedback received: rating={feedback.rating} session={feedback.session_id}")
    return {"status": "success", "message": "Thank you for your feedback!"}


# ---------------------------------------------------------------------------
# Quote engine
# ---------------------------------------------------------------------------


@router.post("/quote/start", response_model=QuoteFlowResponse)
async def quote_start(
    request: QuoteStartRequest, api_key: str = Depends(verify_api_key)
):
    """Return the question flow for a given insurance product."""
    flow = FLOWS.get(request.flow_id)
    if not flow:
        raise AppException(
            status_code=404,
            error_code="QUOTE_FLOW_NOT_FOUND",
            detail=f"No quote flow found for '{request.flow_id}'",
        )
    return QuoteFlowResponse(**flow.to_dict())


@router.post("/quote/calculate", response_model=QuoteResponse)
async def quote_calculate(
    request: QuoteRequest, api_key: str = Depends(verify_api_key)
):
    """Calculate a premium from the user's answers."""
    flow = FLOWS.get(request.flow_id)
    if not flow:
        raise AppException(
            status_code=404,
            error_code="QUOTE_FLOW_NOT_FOUND",
            detail=f"No quote flow found for '{request.flow_id}'",
        )

    # Validate that all required question ids are present
    required_ids = {q.id for q in flow.questions}
    missing = required_ids - set(request.answers.keys())
    if missing:
        raise AppException(
            status_code=422,
            error_code="QUOTE_MISSING_ANSWERS",
            detail=f"Missing answers for: {', '.join(sorted(missing))}",
        )

    try:
        result = calculate_quote(request.flow_id, request.answers)
    except Exception as e:
        logger.error(f"Quote calculation failed: {e}")
        raise ServiceUnavailableError("Could not calculate quote. Please try again.")

    return QuoteResponse(**result)
