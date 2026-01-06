"""Channel sender abstraction for sending messages through different channels."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.models.message import MessageChannel
from app.services.instagram_service import InstagramService
from app.storage.dynamodb import DynamoDBClient

logger = logging.getLogger(__name__)


class ChannelSender(ABC):
    """Abstract base class for channel senders."""

    @abstractmethod
    async def send_message(
        self, conversation_id: str, message_text: str, **kwargs
    ) -> None:
        """Send message through the channel."""
        pass


class WebChatSender(ChannelSender):
    """Sender for web chat channel (WebSocket)."""

    def __init__(self, dynamodb: DynamoDBClient):
        """Initialize web chat sender."""
        self.dynamodb = dynamodb

    async def send_message(
        self, conversation_id: str, message_text: str, **kwargs
    ) -> None:
        """Send message via WebSocket."""
        # WebSocket messages are sent through the connection manager
        # This is handled in the websocket.py endpoint
        # For now, we just log - actual sending happens via WebSocket connection
        logger.info(
            f"WebChat message prepared for conversation {conversation_id}: {message_text[:50]}..."
        )
        # The message is already saved to DB in AgentService
        # WebSocket will broadcast it to connected clients


class InstagramSender(ChannelSender):
    """Sender for Instagram channel."""

    def __init__(
        self,
        instagram_service: InstagramService,
        dynamodb: DynamoDBClient,
    ):
        """Initialize Instagram sender."""
        self.instagram_service = instagram_service
        self.dynamodb = dynamodb

    async def send_message(
        self,
        conversation_id: str,
        message_text: str,
        binding_id: Optional[str] = None,
        external_user_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Send message via Instagram Graph API."""
        if not binding_id or not external_user_id:
            # Try to get from conversation
            conversation = await self.dynamodb.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            # Handle both enum and string channel (from DynamoDB)
            conversation_channel = (
                conversation.channel.value
                if hasattr(conversation.channel, "value")
                else str(conversation.channel)
            )
            if conversation_channel != MessageChannel.INSTAGRAM.value:
                raise ValueError(
                    f"Conversation {conversation_id} is not an Instagram conversation"
                )

            # Find binding by agent_id
            from app.services.channel_binding_service import ChannelBindingService
            from app.storage.secrets import get_secrets_manager

            secrets_manager = get_secrets_manager()
            binding_service = ChannelBindingService(self.dynamodb, secrets_manager)

            bindings = await binding_service.get_bindings_by_agent(
                agent_id=conversation.agent_id,
                channel_type=MessageChannel.INSTAGRAM.value,
                active_only=True,
            )

            if not bindings:
                raise ValueError(
                    f"No active Instagram binding found for agent {conversation.agent_id}"
                )

            binding_id = bindings[0].binding_id
            external_user_id = conversation.external_user_id

        if not external_user_id:
            raise ValueError("external_user_id is required for Instagram messages")

        # Send message via Instagram service
        await self.instagram_service.send_message(
            binding_id=binding_id,
            recipient_id=external_user_id,
            message_text=message_text,
        )

        # Note: Agent message is already saved in AgentService.process_message
        # before calling ChannelSender.send_message, so we don't save it again here


def get_channel_sender(
    channel: MessageChannel,
    dynamodb: DynamoDBClient,
    instagram_service: Optional[InstagramService] = None,
) -> ChannelSender:
    """Get appropriate channel sender for the given channel."""
    if channel == MessageChannel.WEB_CHAT:
        return WebChatSender(dynamodb)
    elif channel == MessageChannel.INSTAGRAM:
        if not instagram_service:
            raise ValueError("InstagramService is required for Instagram channel")
        return InstagramSender(instagram_service, dynamodb)
    else:
        raise ValueError(f"Unsupported channel: {channel}")

