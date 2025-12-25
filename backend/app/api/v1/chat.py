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
from app.models.message import Message, MessageRole
from app.services.agent_service import create_agent_service

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
        status=ConversationStatus.AI_ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    await deps.dynamodb.create_conversation(conversation)

    return CreateConversationResponse(
        conversation_id=conversation_id,
        agent_id=request.agent_id,
        status=conversation.status.value,
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
    if conversation.status == ConversationStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Conversation is closed")

    # Create user message
    message_id = str(uuid.uuid4())
    user_message = Message(
        message_id=message_id,
        conversation_id=conversation_id,
        agent_id=conversation.agent_id,
        role=MessageRole.USER,
        content=request.content,
        timestamp=datetime.utcnow(),
    )

    await deps.dynamodb.create_message(user_message)

    # Get agent configuration
    agent_data = await deps.dynamodb.get_agent(conversation.agent_id)
    if not agent_data or "config" not in agent_data:
        raise HTTPException(status_code=404, detail="Agent not found or invalid configuration")

    agent_config = AgentConfig.from_dict(agent_data["config"])

    # Get conversation history
    history_messages = await deps.dynamodb.list_messages(
        conversation_id=conversation_id,
        limit=10,
    )
    conversation_history = [
        {
            "role": msg.role.value,
            "content": msg.content,
        }
        for msg in history_messages
    ]

    # Process message through agent service
    agent_service = create_agent_service(agent_config, deps.dynamodb)
    result = await agent_service.process_message(
        user_message=request.content,
        conversation_id=conversation_id,
        conversation_history=conversation_history,
    )

    # Handle escalation
    if result.get("escalate"):
        # Status already updated in agent_service, just return user message
        # Return user message with escalation notice
        return SendMessageResponse(
            message_id=message_id,
            role=user_message.role.value,
            content=request.content,
            timestamp=user_message.timestamp.isoformat(),
        )

    # Create agent response message
    agent_response = result.get("response", "I apologize, but I couldn't generate a response.")
    agent_message_id = str(uuid.uuid4())
    agent_message = Message(
        message_id=agent_message_id,
        conversation_id=conversation_id,
        agent_id=conversation.agent_id,
        role=MessageRole.AGENT,
        content=agent_response,
        timestamp=datetime.utcnow(),
        metadata={"rag_context_used": result.get("rag_context_used", False)},
    )

    await deps.dynamodb.create_message(agent_message)

    # Update conversation status if needed
    if conversation.status != ConversationStatus.AI_ACTIVE:
        await deps.dynamodb.update_conversation(
            conversation_id=conversation_id,
            status=ConversationStatus.AI_ACTIVE,
        )

    return SendMessageResponse(
        message_id=agent_message_id,
        role=agent_message.role.value,
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

    messages = await deps.dynamodb.list_messages(conversation_id, limit=limit)
    return messages

