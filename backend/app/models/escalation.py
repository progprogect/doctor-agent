"""Escalation models."""

from enum import Enum

from pydantic import BaseModel, Field


class EscalationType(str, Enum):
    """Type of escalation."""

    URGENT = "urgent"
    MEDICAL = "medical"
    BOOKING = "booking"
    REPEAT_PATIENT = "repeat_patient"
    NONE = "none"


class EscalationDecision(BaseModel):
    """Escalation decision from LLM."""

    needs_escalation: bool = Field(..., description="Whether escalation is needed")
    escalation_type: EscalationType = Field(
        default=EscalationType.NONE, description="Type of escalation"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    reason: str = Field(..., description="Reason for escalation decision")
    suggested_action: str = Field(
        ..., description="Suggested action to take"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True

