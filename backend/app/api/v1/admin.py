"""Admin API endpoints."""

import logging
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
from app.config import get_settings
from app.dependencies import CommonDependencies
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageChannel, MessageRole
from app.services.channel_binding_service import ChannelBindingService
from app.services.channel_sender import get_channel_sender
from app.services.instagram_service import InstagramService
from app.storage.secrets import get_secrets_manager
from app.utils.enum_helpers import get_enum_value

logger = logging.getLogger(__name__)

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


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    deps: CommonDependencies = Depends(),
    _admin: str = require_admin(),
):
    """Get conversation by ID (admin view)."""
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
    return conversation


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

    try:
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

        # Get status value safely (handle both enum and string)
        status_value = (
            get_enum_value(updated.status) if updated else ConversationStatus.HUMAN_ACTIVE.value
        )
        
        return HandoffResponse(
            conversation_id=conversation_id,
            status=status_value,
            message="Conversation handed off to human",
        )
    except Exception as e:
        logger.error(f"Error handing off conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handoff conversation: {str(e)}",
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

    try:
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

        # Get status value safely (handle both enum and string)
        status_value = (
            get_enum_value(updated.status) if updated else ConversationStatus.AI_ACTIVE.value
        )
        
        return {
            "conversation_id": conversation_id,
            "status": status_value,
            "message": "Conversation returned to AI",
        }
    except Exception as e:
        logger.error(f"Error returning conversation to AI: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to return conversation to AI: {str(e)}",
        )


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
    status_value = get_enum_value(conversation.status)
    if status_value not in [
        ConversationStatus.NEEDS_HUMAN.value,
        ConversationStatus.HUMAN_ACTIVE.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin can only send messages when conversation status is NEEDS_HUMAN or HUMAN_ACTIVE",
        )

    try:
        # Create admin message
        message_id = str(uuid.uuid4())
        admin_message = Message(
            message_id=message_id,
            conversation_id=conversation_id,
            agent_id=conversation.agent_id,
            role=MessageRole.ADMIN,
            content=request.content,
            channel=conversation.channel,
            external_user_id=conversation.external_user_id,
            timestamp=datetime.utcnow(),
        )

        # #region agent log
        import json
        with open('/Users/mikitavalkunovich/Desktop/Doctor Agent/doctor-agent/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B","location":"admin.py:300","message":"Before create_message","data":{"conversation_id":conversation_id,"message_id":message_id,"content":request.content[:50]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        await deps.dynamodb.create_message(admin_message)
        # #region agent log
        with open('/Users/mikitavalkunovich/Desktop/Doctor Agent/doctor-agent/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B","location":"admin.py:302","message":"After create_message","data":{"conversation_id":conversation_id,"message_id":message_id},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        
        # Verify message was saved by reading it back
        # #region agent log
        verify_msg = await deps.dynamodb.get_message(message_id)
        with open('/Users/mikitavalkunovich/Desktop/Doctor Agent/doctor-agent/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"admin.py:307","message":"Message verification after save","data":{"message_id":message_id,"found":verify_msg is not None,"role":verify_msg.role.value if verify_msg and hasattr(verify_msg.role, 'value') else str(verify_msg.role) if verify_msg else None},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        
        # Check messages list immediately after save
        # #region agent log
        msgs_after_save = await deps.dynamodb.list_messages(conversation_id, limit=100)
        with open('/Users/mikitavalkunovich/Desktop/Doctor Agent/doctor-agent/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"admin.py:313","message":"Messages list after save","data":{"conversation_id":conversation_id,"count":len(msgs_after_save),"message_ids":[m.message_id for m in msgs_after_save[:5]],"contains_new":message_id in [m.message_id for m in msgs_after_save]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion

        # Determine channel and send message accordingly
        conversation_channel = get_enum_value(conversation.channel)
        
        if conversation_channel == MessageChannel.INSTAGRAM.value:
            # Send via Instagram API for Instagram conversations
            try:
                # Create Instagram service and sender
                settings = get_settings()
                secrets_manager = get_secrets_manager()
                binding_service = ChannelBindingService(deps.dynamodb, secrets_manager)
                instagram_service = InstagramService(binding_service, deps.dynamodb, settings)
                
                # Convert string back to enum for get_channel_sender
                channel_enum = MessageChannel(conversation_channel) if isinstance(conversation_channel, str) else conversation.channel
                instagram_sender = get_channel_sender(
                    channel_enum, deps.dynamodb, instagram_service
                )
                
                # Send message via Instagram API
                await instagram_sender.send_message(
                    conversation_id=conversation_id,
                    message_text=request.content,
                )
                
                logger.info(f"Sent admin message to Instagram conversation {conversation_id}")
            except ValueError as e:
                # No binding or missing external_user_id - return clear error
                logger.error(f"Failed to send Instagram message: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot send message to Instagram conversation: {str(e)}",
                )
            except Exception as instagram_error:
                # Instagram API error - log but don't fail (message already saved)
                logger.error(
                    f"Failed to send message via Instagram API: {instagram_error}",
                    exc_info=True,
                )
                # Message is already saved in DB, so we continue
        else:
            # Send via WebSocket for web chat (don't fail if WebSocket is not connected)
            try:
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
            except Exception as ws_error:
                # Log but don't fail the request if WebSocket fails
                logger.warning(f"Failed to send message via WebSocket: {ws_error}")

        # Create audit log
        await deps.dynamodb.create_audit_log(
            admin_id=request.admin_id,
            action="send_message",
            resource_type="conversation",
            resource_id=conversation_id,
            metadata={"message_id": message_id},
        )

        # Handle both enum and string role (from DynamoDB)
        role_value = get_enum_value(admin_message.role)
        return SendAdminMessageResponse(
            message_id=message_id,
            role=role_value,
            content=admin_message.content,
            timestamp=admin_message.timestamp.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error sending admin message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send admin message: {str(e)}",
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

