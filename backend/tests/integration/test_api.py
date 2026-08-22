"""Integration tests against the full app stack (TestClient + lifespan).

The generator and retriever are stubbed by conftest, so these tests exercise
routing, validation, auth, persistence and middleware without any LLM or
network calls.
"""
import json
import sqlite3

from app.core.config import settings
from conftest import API_KEY, AUTH_HEADERS, CANNED_ANSWER


def _chat_payload(message="What does motor insurance cover?", session_id=None):
    body = {"message": message}
    if session_id:
        body["session_id"] = session_id
    return body


# ------------------------------------------------------------------ #
# Health / observability
# ------------------------------------------------------------------ #
def test_health_shallow(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_health_ready_deep(client):
    resp = client.get("/api/v1/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["components"]["vector_store"] is True
    assert body["components"]["llm_client"] is True
    assert body["components"]["database"] is True
    assert "uptime_seconds" in body["system"]


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text


def test_request_id_echoed(client):
    resp = client.get(
        "/api/v1/health", headers={"X-Request-ID": "test-correlation-123"}
    )
    assert resp.headers.get("X-Request-ID") == "test-correlation-123"


# ------------------------------------------------------------------ #
# Chat
# ------------------------------------------------------------------ #
def test_chat_success_with_sources_and_session(client):
    resp = client.post("/api/v1/chat", json=_chat_payload(), headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == CANNED_ANSWER
    assert body["session_id"]
    assert len(body["sources"]) <= 3
    first = body["sources"][0]
    assert {"text", "score", "source"} <= set(first.keys())


def test_chat_memory_persists_across_turns(client):
    session_id = "test-memory-session"
    for turn in ("First question", "Follow-up question"):
        resp = client.post(
            "/api/v1/chat",
            json=_chat_payload(turn, session_id=session_id),
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["session_id"] == session_id

    resp = client.get(
        f"/api/v1/conversations/{session_id}/history", headers=AUTH_HEADERS
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == session_id
    assert len(body["messages"]) == 4
    assert [m["role"] for m in body["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert body["messages"][0]["content"] == "First question"
    assert body["messages"][1]["content"] == CANNED_ANSWER


def test_chat_stream_sse_events(client):
    resp = client.post(
        "/api/v1/chat/stream", json=_chat_payload(), headers=AUTH_HEADERS
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = [
        json.loads(line[len("data: "):])
        for line in resp.text.splitlines()
        if line.startswith("data: ")
    ]
    types = [e["type"] for e in events]
    assert types[0] == "start"
    assert "sources" in types
    assert "token" in types
    assert types[-1] == "end"
    tokens = "".join(e["content"] for e in events if e["type"] == "token")
    assert tokens == CANNED_ANSWER


# ------------------------------------------------------------------ #
# Feedback
# ------------------------------------------------------------------ #
def test_feedback_is_persisted(client):
    resp = client.post(
        "/api/v1/feedback",
        json={"session_id": "test-feedback-session", "rating": 5, "comment": "Great!"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    db_path = settings.database_url.split("sqlite:///")[-1]
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT rating, comment FROM feedback "
            "WHERE session_id = 'test-feedback-session'"
        ).fetchone()
    assert row == (5, "Great!")


def test_feedback_rejects_out_of_range_rating(client):
    resp = client.post(
        "/api/v1/feedback", json={"rating": 9}, headers=AUTH_HEADERS
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "VALIDATION_ERROR"


# ------------------------------------------------------------------ #
# Auth, validation, rate limiting
# ------------------------------------------------------------------ #
def test_invalid_api_key_returns_403(client):
    resp = client.post(
        "/api/v1/chat",
        json=_chat_payload(),
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 403


def test_missing_api_key_returns_403(client):
    resp = client.post("/api/v1/chat", json=_chat_payload())
    assert resp.status_code == 403


def test_oversized_message_rejected(client):
    resp = client.post(
        "/api/v1/chat",
        json=_chat_payload("x" * (settings.max_message_length + 1)),
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "VALIDATION_ERROR"


def test_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_chat", 1)

    first = client.post("/api/v1/chat", json=_chat_payload(), headers=AUTH_HEADERS)
    assert first.status_code == 200

    second = client.post("/api/v1/chat", json=_chat_payload(), headers=AUTH_HEADERS)
    assert second.status_code == 429
    assert second.json()["error_code"] == "RATE_LIMIT_ERROR"
    assert int(second.headers["Retry-After"]) >= 1
