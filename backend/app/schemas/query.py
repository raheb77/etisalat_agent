from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(..., description="User question")
    category_hint: Optional[str] = Field(None, description="Optional category hint")
    locale: str = Field("ar-SA", description="Locale")
    channel: str = Field("csr_ui", description="Channel")

    @field_validator("question")
    @classmethod
    def question_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("question must be non-empty")
        return value


class Citation(BaseModel):
    source: str
    chunk_id: str
    score: float
    snippet: Optional[str] = None


class HandoffPayload(BaseModel):
    team: str
    summary: str
    evidence: List[str]


class QueryResponse(BaseModel):
    answer: str
    steps: List[str]
    citations: List[Citation]
    confidence: float
    category: str
    risk_level: str
    handoff: bool
    handoff_reason: str = ""
    handoff_payload: Optional[HandoffPayload] = None
    debug: Optional[dict] = None

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value
