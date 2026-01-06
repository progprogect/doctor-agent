"""Admin API endpoints."""

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.auth import require_admin
from app.api.exceptions import ConversationNotFoundError
from app.api.schemas import ConversationIDValidator
from app.api.websocket import connection_manager
from app.dependencies import CommonDependencies
from app.models.conversation import ConversationStatus
from app.models.message import Message, MessageChannel, MessageRole

router = APIRouter()


class HandoffRequest(BaseModel):
    """Request to handoff conversation to human."""

    admin_id: str = Field(..., description="Admin user ID", min_length=1)
    reason: Optional[str] = Field(
        None, description="Reason for handoff", max_length=500
    )


class HandoffResponse(BaseModel):
    """Response for handoff."""

    conversation_id: str
    status: str
    message: str


@router.get("/conversations")
async def list_conversations(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by conversation status"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of conversations"),
    deps: CommonDependencies = Depends(),
    _admin: str = require_admin(),
):
    """List conversations (admin view)."""
    status_enum = None
    if status:
        try:
            status_enum = ConversationStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Valid values: {', '.join([s.value for s in ConversationStatus])}",
            )

    conversations = await deps.dynamodb.list_conversations(
        agent_id=agent_id,
        status=status_enum,
        limit=limit,
    )
    return conversations


@router.post(
    "/conversations/{conversation_id}/handoff",
    response_model=HandoffResponse,
    status_code=status.HTTP_200_OK,
)
async def handoff_conversation(
    conversation_id: str,
    request: HandoffRequest,
    deps: CommonDependencies = Depends(),
    _admin: str = require_admin(),
):
    """Handoff conversation to human admin."""
    # Validate UUID format
    try:
        UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    conversation = await deps.dynamodb.get_conversation(conversation_id)
    if not conversation:
        raise ConversationNotFoundError(conversation_id)

    # Update conversation status
    updated = await deps.dynamodb.update_conversation(
        conversation_id=conversation_id,
        status=ConversationStatus.HUMAN_ACTIVE,
        handoff_reason=request.reason or "Manual handoff",
    )

    # Create audit log
    await deps.dynamodb.create_audit_log(
        admin_id=request.admin_id,
        action="handoff",
        resource_type="conversation",
        resource_id=conversation_id,
        metadata={"reason": request.reason},
    )

    return HandoffResponse(
        conversation_id=conversation_id,
        status=updated.status.value if updated else ConversationStatus.HUMAN_ACTIVE.value,
        message="Conversation handed off to human",
    )


class ReturnToAIRequest(BaseModel):
    """Request to return conversation to AI."""

    admin_id: str = Field(..., description="Admin user ID", min_length=1)


@router.post("/conversations/{conversation_id}/return")
async def return_to_ai(
    conversation_id: str,
    request: ReturnToAIRequest,
    deps: CommonDependencies = Depends(),
    _admin: str = require_admin(),
):
    """Return conversation to AI."""
    # Validate UUID format
    try:
        UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    conversation = await deps.dynamodb.get_conversation(conversation_id)
    if not conversation:
        raise ConversationNotFoundError(conversation_id)

    # Update conversation status
    updated = await deps.dynamodb.update_conversation(
        conversation_id=conversation_id,
        status=ConversationStatus.AI_ACTIVE,
    )

    # Create audit log
    await deps.dynamodb.create_audit_log(
        admin_id=request.admin_id,
        action="return_to_ai",
        resource_type="conversation",
        resource_id=conversation_id,
    )

    return {
        "conversation_id": conversation_id,
        "status": updated.status.value if updated else ConversationStatus.AI_ACTIVE.value,
        "message": "Conversation returned to AI",
    }


@router.get("/audit")
async def get_audit_logs(
    admin_id: Optional[str] = Query(None, description="Filter by admin ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of logs"),
    deps: CommonDependencies = Depends(),
    _admin: str = require_admin(),
):
    """Get audit logs."""
    logs = await deps.dynamodb.list_audit_logs(
        admin_id=admin_id,
        resource_type=resource_type,
        limit=limit,
    )
    return logs


class SendAdminMessageRequest(BaseModel):
    """Request to send admin message."""

    admin_id: str = Field(..., description="Admin user ID", min_length=1)
    content: str = Field(..., description="Message content", min_length=1, max_length=10000)


class SendAdminMessageResponse(BaseModel):
    """Response for admin message."""

    message_id: str
    role: str
    content: str
    timestamp: str


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=SendAdminMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_admin_message(
    conversation_id: str,
    request: SendAdminMessageRequest,
    deps: CommonDependencies = Depends(),
    _admin: str = require_admin(),
):
    """Send a message as admin in a conversation."""
    # Validate UUID format
    try:
        UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    conversation = await deps.dynamodb.get_conversation(conversation_id)
    if not conversation:
        raise ConversationNotFoundError(conversation_id)

    # Check conversation status - admin can only send messages when human is handling
    status_value = (
        conversation.status.value
        if hasattr(conversation.status, "value")
        else str(conversation.status)
    )
    if status_value not in [
        ConversationStatus.NEEDS_HUMAN.value,
        ConversationStatus.HUMAN_ACTIVE.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin can only send messages when conversation status is NEEDS_HUMAN or HUMAN_ACTIVE",
        )

    # Create admin message
    message_id = str(uuid.uuid4())
    admin_message = Message(
        message_id=message_id,
        conversation_id=conversation_id,
        agent_id=conversation.agent_id,
        role=MessageRole.ADMIN,
        content=request.content,
        channel=conversation.channel,
        timestamp=datetime.utcnow(),
    )

    await deps.dynamodb.create_message(admin_message)

    # Send via WebSocket if connected
    await connection_manager.send_message(
        conversation_id,
        {
            "type": "message",
            "message_id": message_id,
            "role": "admin",
            "content": request.content,
            "timestamp": admin_message.timestamp.isoformat(),
        },
    )

    # Create audit log
    await deps.dynamodb.create_audit_log(
        admin_id=request.admin_id,
        action="send_message",
        resource_type="conversation",
        resource_id=conversation_id,
        metadata={"message_id": message_id},
    )

    # Handle both enum and string role (from DynamoDB)
    role_value = (
        admin_message.role.value
        if hasattr(admin_message.role, "value")
        else str(admin_message.role)
    )
    return SendAdminMessageResponse(
        message_id=message_id,
        role=role_value,
        content=admin_message.content,
        timestamp=admin_message.timestamp.isoformat(),
    )


@router.get("/stats")
async def get_stats(
    deps: CommonDependencies = Depends(),
    _admin: str = require_admin(),
):
    """Get basic statistics."""
    # Get all conversations
    all_conversations = await deps.dynamodb.list_conversations(limit=1000)

    stats = {
        "total_conversations": len(all_conversations),
        "ai_active": sum(1 for c in all_conversations if c.status == ConversationStatus.AI_ACTIVE),
        "needs_human": sum(1 for c in all_conversations if c.status == ConversationStatus.NEEDS_HUMAN),
        "human_active": sum(1 for c in all_conversations if c.status == ConversationStatus.HUMAN_ACTIVE),
        "closed": sum(1 for c in all_conversations if c.status == ConversationStatus.CLOSED),
    }

    return stats

