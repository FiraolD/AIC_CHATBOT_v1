"""Shared test fixtures: hermetic app with canned RAG, no external calls.

Environment variables are set BEFORE the app is imported so the
pydantic-settings singleton picks them up (env vars override .env).
The vector store module is stubbed out so tests never load the
sentence-transformers embeddings model or touch FAISS.
"""
import os
import sys
import tempfile
import types
from pathlib import Path

import pytest

# --- Environment must be ready before the app is imported -------------- #
_TEST_DB = Path(tempfile.gettempdir()) / f"awash_test_{os.getpid()}.db"

os.environ.update({
    "ENVIRONMENT": "testing",
    "DEBUG": "false",
    "LOG_LEVEL": "WARNING",
    "API_KEY": "test-api-key",
    "LLM_PROVIDER": "groq",
    "GROQ_API_KEY": "test-groq-key",
    "LLM_MODEL": "test-model",
    "DATABASE_URL": f"sqlite:///{_TEST_DB.as_posix()}",
})

# Ensure the backend package root is importable regardless of launch dir
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# --- Stub the vector store BEFORE any app module imports it ------------ #
class _FakeVectorStore:
    """Stands in for the real FAISS + embeddings singleton."""

    vector_store = object()  # truthy -> readiness reports vector_store up


_fake_module = types.ModuleType("app.rag.vector_store")
_fake_module.vector_store = _FakeVectorStore()
sys.modules["app.rag.vector_store"] = _fake_module

from app.core.middleware.rate_limit import in_memory_window  # noqa: E402
from app.main import app  # noqa: E402
from app.rag.generator import generator  # noqa: E402
from app.rag.retriever import RetrievalResult, retriever  # noqa: E402

API_KEY = "test-api-key"
AUTH_HEADERS = {"X-API-Key": API_KEY}

CANNED_TOKENS = ["Awash ", "Insurance ", "offers ", "motor ", "coverage."]
CANNED_ANSWER = "".join(CANNED_TOKENS)
CANNED_SOURCES = [
    {
        "text": "Motor insurance covers vehicles against damage.",
        "score": 0.95,
        "source": "insurance_knowledge.csv",
    },
    {
        "text": "Claims must be reported within 30 days.",
        "score": 0.87,
        "source": "insurance_knowledge.csv",
    },
]


async def _fake_stream_answer(query, context, history=None):
    """Deterministic generator: no LLM network calls."""
    for token in CANNED_TOKENS:
        yield token


async def _fake_get_result(query):
    """Deterministic retrieval: no embeddings/FAISS/BM25 work."""
    return RetrievalResult(context="canned context", sources=list(CANNED_SOURCES))


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as c:  # context manager runs the lifespan hooks
        yield c


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Isolate sliding-window state between tests."""
    in_memory_window.reset()
    yield
    in_memory_window.reset()


@pytest.fixture(autouse=True)
def _stub_rag(monkeypatch):
    """Replace generator and retriever so no external call is ever made."""
    monkeypatch.setattr(generator, "stream_answer", _fake_stream_answer)
    monkeypatch.setattr(retriever, "get_result", _fake_get_result)
