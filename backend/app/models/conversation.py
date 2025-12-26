"""Conversation models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Status of a conversation."""

    AI_ACTIVE = "AI_ACTIVE"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    HUMAN_ACTIVE = "HUMAN_ACTIVE"
    CLOSED = "CLOSED"


class Conversation(BaseModel):
    """Conversation model."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    agent_id: str = Field(..., description="Agent ID this conversation belongs to")
    status: ConversationStatus = Field(
        default=ConversationStatus.AI_ACTIVE, description="Current conversation status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = Field(None, description="When conversation was closed")
    handoff_reason: Optional[str] = Field(
        None, description="Reason for handoff to human"
    )
    request_type: Optional[str] = Field(
        None, description="Type of request: info, booking, escalation"
    )
    ttl: Optional[int] = Field(
        None, description="TTL timestamp for DynamoDB (created_at + 48h)"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}




