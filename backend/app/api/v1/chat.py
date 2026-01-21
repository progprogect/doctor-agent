"""Chat API endpoints."""

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.exceptions import AgentNotFoundError, ConversationNotFoundError
from app.api.schemas import (
    AgentIDValidator,
    ConversationIDValidator,
    MessageContentValidator,
)
from app.dependencies import CommonDependencies
from app.models.agent_config import AgentConfig
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageChannel, MessageRole
from app.services.agent_service import create_agent_service
from app.services.channel_sender import get_channel_sender
from app.services.channel_binding_service import ChannelBindingService
from app.services.instagram_service import InstagramService
from app.config import get_settings
from app.storage.secrets import get_secrets_manager
from app.utils.enum_helpers import get_enum_value

router = APIRouter()


class CreateConversationRequest(BaseModel, AgentIDValidator):
    """Request to create a conversation."""

    agent_id: str = Field(..., description="Agent ID")


class CreateConversationResponse(BaseModel):
    """Response for created conversation."""

    conversation_id: str
    agent_id: str
    status: str


class SendMessageRequest(BaseModel, MessageContentValidator):
    """Request to send a message."""

    content: str = Field(..., description="Message content", min_length=1, max_length=10000)


class SendMessageResponse(BaseModel):
    """Response for sent message."""

    message_id: str
    role: str
    content: str
    timestamp: str


@router.post(
    "/conversations",
    response_model=CreateConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    request: CreateConversationRequest,
    deps: CommonDependencies = Depends(),
):
    """Create a new conversation."""
    # Verify agent exists
    agent_data = await deps.dynamodb.get_agent(request.agent_id)
    if not agent_data:
        raise AgentNotFoundError(request.agent_id)

    conversation_id = str(uuid.uuid4())
    conversation = Conversation(
        conversation_id=conversation_id,
        agent_id=request.agent_id,
        channel=MessageChannel.WEB_CHAT,  # Web chat is default channel
        status=ConversationStatus.AI_ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    await deps.dynamodb.create_conversation(conversation)

    # Handle both enum and string status (from DynamoDB)
    status_value = get_enum_value(conversation.status)
    return CreateConversationResponse(
        conversation_id=conversation_id,
        agent_id=request.agent_id,
        status=status_value,
    )


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    deps: CommonDependencies = Depends(),
):
    """Get conversation by ID."""
    # Validate UUID format
    try:
        uuid.UUID(conversation_id)
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
    "/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    deps: CommonDependencies = Depends(),
):
    """Send a message in a conversation."""
    # Validate UUID format
    try:
        uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    # Verify conversation exists
    conversation = await deps.dynamodb.get_conversation(conversation_id)
    if not conversation:
        raise ConversationNotFoundError(conversation_id)

    # Check if conversation is active
    # Handle both enum and string status (from DynamoDB)
    status_value = get_enum_value(conversation.status)
    if status_value == ConversationStatus.CLOSED.value:
        raise HTTPException(status_code=400, detail="Conversation is closed")

    # Create user message
    message_id = str(uuid.uuid4())
    user_message = Message(
        message_id=message_id,
        conversation_id=conversation_id,
        agent_id=conversation.agent_id,
        role=MessageRole.USER,
        content=request.content,
        channel=conversation.channel,
        external_user_id=conversation.external_user_id,
        timestamp=datetime.utcnow(),
    )

    await deps.dynamodb.create_message(user_message)

    # Check if conversation is handled by human - don't process with agent
    if status_value in [
        ConversationStatus.NEEDS_HUMAN.value,
        ConversationStatus.HUMAN_ACTIVE.value,
    ]:
        # Return user message without agent processing
        role_value = get_enum_value(user_message.role)
        return SendMessageResponse(
            message_id=message_id,
            role=role_value,
            content=user_message.content,
            timestamp=user_message.timestamp.isoformat(),
        )

    # Get agent configuration
    agent_data = await deps.dynamodb.get_agent(conversation.agent_id)
    if not agent_data or "config" not in agent_data:
        raise HTTPException(status_code=404, detail="Agent not found or invalid configuration")

    agent_config = AgentConfig.from_dict(agent_data["config"])

    # Get conversation history (last 50 messages for context)
    # Note: list_messages returns messages in reverse order (newest first) by default
    # We need chronological order (oldest first) for LLM context
    history_messages = await deps.dynamodb.list_messages(
        conversation_id=conversation_id,
        limit=50,
        reverse=True,  # Get newest first (default)
    )
    # Reverse to get chronological order (oldest first) for LLM context
    # After reverse: [oldest_message, ..., newest_message]
    conversation_history = [
        {
            "role": get_enum_value(msg.role),
            "content": msg.content,
        }
        for msg in reversed(history_messages)  # Reverse to chronological order (oldest first)
    ]
    
    # CRITICAL FIX: Exclude the current user message from history
    # The current message is already saved to DB and will be passed as 'input' to LLM
    # Including it in chat_history causes duplication and context confusion
    if conversation_history:
        last_msg = conversation_history[-1]
        # Check if last message is from user and matches current message
        if (
            last_msg.get("role", "").lower() == "user"
            and last_msg.get("content", "").strip() == request.content.strip()
        ):
            # Remove the duplicate current message from history
            conversation_history = conversation_history[:-1]

    # Get channel sender for the conversation's channel
    # Handle both enum and string channel (from DynamoDB)
    conversation_channel = get_enum_value(conversation.channel)
    
    instagram_service = None
    if conversation_channel != MessageChannel.WEB_CHAT.value:
        # Create Instagram service if needed
        settings = get_settings()
        secrets_manager = get_secrets_manager()
        binding_service = ChannelBindingService(deps.dynamodb, secrets_manager)
        instagram_service = InstagramService(binding_service, deps.dynamodb, settings)
    
    # Convert string back to enum for get_channel_sender
    channel_enum = MessageChannel(conversation_channel) if isinstance(conversation_channel, str) else conversation.channel
    channel_sender = get_channel_sender(
        channel_enum, deps.dynamodb, instagram_service
    )

    # Process message through agent service
    agent_service = create_agent_service(agent_config, deps.dynamodb, channel_sender)
    result = await agent_service.process_message(
        user_message=request.content,
        conversation_id=conversation_id,
        conversation_history=conversation_history,
    )

    # Handle escalation
    if result.get("escalate"):
        # Status already updated in agent_service, just return user message
        # Return user message with escalation notice
        # Handle both enum and string role (from DynamoDB)
        role_value = get_enum_value(user_message.role)
        return SendMessageResponse(
            message_id=message_id,
            role=role_value,
            content=request.content,
            timestamp=user_message.timestamp.isoformat(),
        )

    # Agent message is already created in agent_service.process_message
    # Use the message_id from result if available, otherwise create new one
    agent_response = result.get("response", "I apologize, but I couldn't generate a response.")
    agent_message_id = result.get("agent_message_id")
    
    # If message wasn't created in agent_service (shouldn't happen, but handle gracefully)
    if not agent_message_id:
        agent_message_id = str(uuid.uuid4())
        agent_message = Message(
            message_id=agent_message_id,
            conversation_id=conversation_id,
            agent_id=conversation.agent_id,
            role=MessageRole.AGENT,
            content=agent_response,
            channel=conversation.channel,
            external_user_id=conversation.external_user_id,
            timestamp=datetime.utcnow(),
            metadata={"rag_context_used": result.get("rag_context_used", False)},
        )
        await deps.dynamodb.create_message(agent_message)

    # Update conversation status if needed
    # Handle both enum and string status (from DynamoDB)
    status_value = get_enum_value(conversation.status)
    if status_value != ConversationStatus.AI_ACTIVE.value:
        await deps.dynamodb.update_conversation(
            conversation_id=conversation_id,
            status=ConversationStatus.AI_ACTIVE,
        )

    # Handle both enum and string role (from DynamoDB)
    role_value = get_enum_value(agent_message.role)
    return SendMessageResponse(
        message_id=agent_message_id,
        role=role_value,
        content=agent_message.content,
        timestamp=agent_message.timestamp.isoformat(),
    )


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of messages"),
    deps: CommonDependencies = Depends(),
):
    """Get messages for a conversation."""
    # Validate UUID format
    try:
        uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    # Verify conversation exists
    conversation = await deps.dynamodb.get_conversation(conversation_id)
    if not conversation:
        raise ConversationNotFoundError(conversation_id)

    # #region agent log
    try:
        import json
        import os
        log_path = '/Users/mikitavalkunovich/Desktop/Doctor Agent/doctor-agent/.cursor/debug.log'
        if os.path.exists(os.path.dirname(log_path)) or os.path.exists('/Users/mikitavalkunovich'):
            with open(log_path, 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A,C","location":"chat.py:314","message":"Before list_messages","data":{"conversation_id":conversation_id,"limit":limit},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except Exception:
        pass
    # #endregion
    messages = await deps.dynamodb.list_messages(conversation_id, limit=limit, reverse=False)
    # #region agent log
    try:
        import json
        import os
        from app.utils.enum_helpers import get_enum_value
        log_path = '/Users/mikitavalkunovich/Desktop/Doctor Agent/doctor-agent/.cursor/debug.log'
        if os.path.exists(os.path.dirname(log_path)) or os.path.exists('/Users/mikitavalkunovich'):
            roles_list = []
            for m in messages[:5]:
                try:
                    roles_list.append(get_enum_value(m.role))
                except:
                    roles_list.append(str(m.role) if hasattr(m, 'role') else 'unknown')
            with open(log_path, 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A,C","location":"chat.py:317","message":"After list_messages","data":{"conversation_id":conversation_id,"count":len(messages),"message_ids":[m.message_id for m in messages[:5]],"roles":roles_list},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except Exception:
        pass
    # #endregion
    return messages

