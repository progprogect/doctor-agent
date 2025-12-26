"""Message models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role."""

    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"


class Message(BaseModel):
    """Message model."""

    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Conversation ID")
    agent_id: str = Field(..., description="Agent ID")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    ttl: Optional[int] = Field(
        None, description="TTL timestamp for DynamoDB (timestamp + 48h)"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}




