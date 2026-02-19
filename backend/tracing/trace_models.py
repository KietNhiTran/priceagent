"""
Pydantic models for agent tracing.

Aligned with:
  - Req 7.1: Audit trail capture
  - Req 7.2: Decision traceability
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InferenceMode(str, Enum):
    REAL = "real"
    FALLBACK = "fallback"


class Decision(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    SEND_TO_REVIEW = "SEND_TO_REVIEW"
    AUTO_REJECT = "AUTO_REJECT"
    NO_ACTION = "NO_ACTION"
    NOT_LLPG = "NOT_LLPG"
    INCOMPLETE = "INCOMPLETE"
    NO_MATCH = "NO_MATCH"


class AgentStep(BaseModel):
    """A single agent execution step within a trace."""
    model_config = ConfigDict(populate_by_name=True)
    
    step_id: str
    trace_id: str = Field(exclude=True)  # Internal only, not serialized to frontend
    agent_name: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = Field(default=None, alias="started_at")
    end_time: Optional[datetime] = Field(default=None, alias="completed_at")
    duration_ms: Optional[int] = None
    input_summary: str = ""
    output_summary: str = ""
    inference_mode: InferenceMode = InferenceMode.FALLBACK
    raw_json: dict[str, Any] = Field(default_factory=dict)


class TraceDecision(BaseModel):
    """Final decision details for an LLPG trace."""
    model_config = ConfigDict(populate_by_name=True)
    
    decision: Decision
    reason_code: str = ""
    beat_price: Optional[float] = None
    rsa_compliant: bool = True
    competitor: str = Field("", alias="competitor_name")
    product_name: str = Field("", alias="our_product_name")
    competitor_price: Optional[float] = None
    own_price: Optional[float] = None
    saving: Optional[float] = None


class AgentTrace(BaseModel):
    """Complete trace of a multi-agent execution."""
    trace_id: str
    session_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_duration_ms: Optional[int] = None
    final_decision: Optional[str] = None
    user_message: str = ""
    steps: list[AgentStep] = Field(default_factory=list)
    decision: Optional[TraceDecision] = None
