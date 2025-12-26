"""Service for conversation management."""

from typing import Optional

from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageRole
from app.services.agent_service import AgentService, create_agent_service
from app.storage.dynamodb import DynamoDBClient


class ConversationService:
    """Service for managing conversations and processing messages."""

    def __init__(self, dynamodb: DynamoDBClient):
        """Initialize conversation service."""
        self.dynamodb = dynamodb

    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
        agent_service: AgentService,
    ) -> dict:
        """Process user message and return agent response."""
        # Get conversation
        conversation = await self.dynamodb.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Get conversation history
        history_messages = await self.dynamodb.list_messages(
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

        # Process through agent service
        result = await agent_service.process_message(
            user_message=user_message,
            conversation_id=conversation_id,
            conversation_history=conversation_history,
        )

        return result

    async def send_agent_response(
        self,
        conversation_id: str,
        agent_response: str,
        metadata: Optional[dict] = None,
    ) -> Message:
        """Create and save agent response message."""
        from datetime import datetime
        import uuid

        # Get conversation to get agent_id
        conversation = await self.dynamodb.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Create agent message
        message_id = str(uuid.uuid4())
        agent_message = Message(
            message_id=message_id,
            conversation_id=conversation_id,
            agent_id=conversation.agent_id,
            role=MessageRole.AGENT,
            content=agent_response,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        await self.dynamodb.create_message(agent_message)

        # Update conversation status if needed
        if conversation.status != ConversationStatus.AI_ACTIVE:
            await self.dynamodb.update_conversation(
                conversation_id=conversation_id,
                status=ConversationStatus.AI_ACTIVE,
            )

        return agent_message




