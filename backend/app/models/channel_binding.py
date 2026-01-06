"""Channel binding models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    """Channel type enumeration."""

    WEB_CHAT = "web_chat"
    INSTAGRAM = "instagram"


class ChannelBinding(BaseModel):
    """Channel binding model."""

    binding_id: str = Field(..., description="Unique binding identifier (UUID)")
    agent_id: str = Field(..., description="Agent ID this binding belongs to")
    channel_type: ChannelType = Field(..., description="Type of channel")
    channel_account_id: str = Field(
        ..., description="Channel account ID (e.g., Instagram Business Account ID)"
    )
    channel_username: Optional[str] = Field(
        None, description="Channel username (e.g., Instagram username) for display"
    )

    # Reference to secret in Secrets Manager (NOT the token itself!)
    secret_name: str = Field(
        ...,
        description="Name of secret in AWS Secrets Manager containing access token",
    )

    # Binding status
    is_active: bool = Field(default=True, description="Whether binding is active")
    is_verified: bool = Field(
        default=False, description="Whether token has been verified via API"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(
        None, description="Admin user ID who created the binding"
    )

    # Additional channel-specific data (without tokens!)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional channel metadata (e.g., app_id, page_id)",
    )

    ttl: Optional[int] = Field(
        None, description="TTL timestamp for DynamoDB (if auto-deletion needed)"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}

