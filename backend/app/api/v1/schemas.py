"""Pydantic schemas for the v1 API."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...core.config import settings

SESSION_ID_PATTERN = r"^[a-zA-Z0-9\-_]{1,64}$"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=settings.max_message_length)
    session_id: Optional[str] = Field(default=None, pattern=SESSION_ID_PATTERN)
    metadata: Optional[Dict[str, Any]] = None


class Source(BaseModel):
    text: str
    score: float
    source: str = "knowledge-base"


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[Source] = []


class StreamEvent(BaseModel):
    type: str  # start | sources | token | end | error
    content: Optional[str] = None


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: Optional[str] = None


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[MessageOut] = []


class FeedbackRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, pattern=SESSION_ID_PATTERN)
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class InsuranceType(BaseModel):
    id: str
    name: str
    icon: str
    description: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(BaseModel):
    status: str  # ready | degraded
    components: Dict[str, Any]
    system: Dict[str, Any]


# ---------------------------------------------------------------------------
# Quote engine
# ---------------------------------------------------------------------------


class QuoteQuestion(BaseModel):
    id: str
    text: str
    type: str  # choice | text
    options: Optional[List[str]] = None


class QuoteFlowResponse(BaseModel):
    flow_id: str
    name: str
    questions: List[QuoteQuestion]


class QuoteStartRequest(BaseModel):
    flow_id: str = Field(pattern=r"^[a-z_]{1,32}$")


class QuoteRequest(BaseModel):
    flow_id: str = Field(pattern=r"^[a-z_]{1,32}$")
    answers: Dict[str, str]


class QuoteResponse(BaseModel):
    product_name: str
    answers: Dict[str, str]
    premium_monthly: float
    premium_annual: float
    breakdown: Dict[str, Any]
