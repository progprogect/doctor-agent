"""Telegram service for handling Telegram Bot messaging."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.config import Settings, get_settings
from app.models.channel_binding import ChannelType
from app.models.conversation import Conversation, ConversationStatus, MarketingStatus
from app.models.message import Message, MessageChannel, MessageRole
from app.services.channel_binding_service import ChannelBindingService
from app.storage.dynamodb import DynamoDBClient
from app.utils.datetime_utils import utc_now
from app.utils.enum_helpers import get_enum_value

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for Telegram Bot messaging integration."""

    TELEGRAM_API_BASE_URL = "https://api.telegram.org/bot"

    def __init__(
        self,
        channel_binding_service: ChannelBindingService,
        dynamodb: DynamoDBClient,
        settings: Settings,
    ):
        """Initialize Telegram service."""
        self.channel_binding_service = channel_binding_service
        self.dynamodb = dynamodb
        self.settings = settings

    async def handle_webhook_event(
        self, payload: dict[str, Any], binding_id: str
    ) -> None:
        """Handle incoming webhook event from Telegram."""
        try:
            # Telegram webhook payload structure:
            # {
            #   "update_id": 123456789,
            #   "message": {
            #     "message_id": 123,
            #     "from": {"id": 123456789, "username": "user", "first_name": "Name"},
            #     "chat": {"id": 123456789, "type": "private"},
            #     "date": 1234567890,
            #     "text": "Hello"
            #   }
            # }

            # Get binding to verify it exists and is active
            binding = await self.channel_binding_service.get_binding(binding_id)
            if not binding:
                logger.warning(f"Binding {binding_id} not found for Telegram webhook")
                return

            if not binding.is_active:
                logger.warning(
                    f"Received message from inactive binding: {binding_id}. Ignoring."
                )
                return

            if binding.channel_type != ChannelType.TELEGRAM:
                logger.warning(
                    f"Binding {binding_id} is not a Telegram binding. Ignoring."
                )
                return

            # Extract message from update
            message_data = payload.get("message")
            if not message_data:
                # Telegram can send other update types (edited_message, callback_query, etc.)
                # We only process regular messages for now
                logger.debug(f"Telegram update without message: {payload.get('update_id')}")
                return

            # Extract message details
            chat = message_data.get("chat", {})
            chat_id = str(chat.get("id"))  # Telegram chat_id can be int or str
            message_text = message_data.get("text", "")
            message_id = message_data.get("message_id")
            from_user = message_data.get("from", {})
            user_id = str(from_user.get("id")) if from_user.get("id") else None

            # Skip messages from bots (to avoid loops)
            if from_user.get("is_bot", False):
                logger.info(
                    f"Ignoring message from bot: chat_id={chat_id}, message_id={message_id}"
                )
                return

            if not chat_id:
                logger.warning(f"Telegram message without chat_id: {message_data}")
                return
            
            # Skip messages without text (photos, documents, stickers, etc.)
            # We only process text messages for now
            if not message_text:
                logger.debug(f"Telegram message without text (chat_id={chat_id}), skipping")
                return

            # Parse timestamp from Telegram (Unix timestamp in seconds)
            message_timestamp = utc_now()
            if "date" in message_data:
                try:
                    telegram_timestamp = message_data["date"]
                    if isinstance(telegram_timestamp, (int, float)):
                        message_timestamp = datetime.fromtimestamp(
                            int(telegram_timestamp), tz=timezone.utc
                        )
                        logger.debug(
                            f"Using timestamp from Telegram webhook: {message_timestamp}"
                        )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Failed to parse Telegram timestamp: {e}, using current time"
                    )

            # Find or create conversation
            conversation = await self._find_or_create_conversation(
                agent_id=binding.agent_id,
                external_user_id=chat_id,  # Use chat_id as external_user_id
                external_conversation_id=None,
            )

            # Create user message
            user_message = Message(
                message_id=str(uuid.uuid4()),
                conversation_id=conversation.conversation_id,
                agent_id=binding.agent_id,
                role=MessageRole.USER,
                content=message_text,
                channel=MessageChannel.TELEGRAM,
                external_message_id=str(message_id) if message_id else None,
                external_user_id=chat_id,
                timestamp=message_timestamp,
            )

            await self.dynamodb.create_message(user_message)

            # Check if conversation is handled by human - don't process with agent
            status_value = get_enum_value(conversation.status)
            if status_value in [
                ConversationStatus.NEEDS_HUMAN.value,
                ConversationStatus.HUMAN_ACTIVE.value,
            ]:
                logger.info(
                    f"Conversation {conversation.conversation_id} is handled by human, skipping agent processing"
                )
                return

            # Process message through agent
            try:
                # Get agent configuration
                agent_data = await self.dynamodb.get_agent(binding.agent_id)
                if not agent_data or "config" not in agent_data:
                    logger.error(f"Agent {binding.agent_id} not found or invalid configuration")
                    return

                from app.models.agent_config import AgentConfig

                agent_config = AgentConfig.from_dict(agent_data["config"])

                # Get conversation history
                history_messages = await self.dynamodb.list_messages(
                    conversation_id=conversation.conversation_id,
                    limit=50,
                    reverse=True,
                )
                conversation_history = [
                    {
                        "role": get_enum_value(msg.role),
                        "content": msg.content,
                    }
                    for msg in reversed(history_messages)
                ]

                # Exclude current user message from history
                if conversation_history:
                    last_msg = conversation_history[-1]
                    if (
                        last_msg.get("role", "").lower() == "user"
                        and last_msg.get("content", "").strip() == message_text.strip()
                    ):
                        conversation_history = conversation_history[:-1]

                # Create channel sender for Telegram
                from app.services.channel_sender import TelegramSender
                from app.services.agent_service import create_agent_service

                telegram_sender = TelegramSender(self, self.dynamodb)

                # Create agent service with channel sender
                agent_service = create_agent_service(
                    agent_config, self.dynamodb, telegram_sender
                )

                result = await agent_service.process_message(
                    user_message=message_text,
                    conversation_id=conversation.conversation_id,
                    conversation_history=conversation_history,
                )

                # Handle escalation
                if result.get("escalate"):
                    logger.info(
                        f"Message escalated for conversation {conversation.conversation_id}"
                    )
                    return

                # Agent response is sent via ChannelSender in AgentService.process_message
                # No need to send manually here

            except Exception as e:
                logger.error(
                    f"Error processing message through agent: {e}", exc_info=True
                )

        except Exception as e:
            logger.error(f"Error handling Telegram webhook event: {e}", exc_info=True)
            raise

    async def _find_or_create_conversation(
        self,
        agent_id: str,
        external_user_id: str,
        external_conversation_id: Optional[str],
    ) -> Conversation:
        """Find existing conversation or create new one."""
        # Try to find existing conversation by external_user_id and agent_id
        try:
            all_conversations = await self.dynamodb.list_conversations(
                agent_id=agent_id,
                limit=100,
            )

            # Find conversation with matching external_user_id
            for conv in all_conversations:
                conv_channel = get_enum_value(conv.channel)
                if (
                    conv_channel == MessageChannel.TELEGRAM.value
                    and conv.external_user_id == external_user_id
                ):
                    logger.info(
                        f"Found existing conversation {conv.conversation_id} for chat {external_user_id}"
                    )
                    return conv
        except Exception as e:
            logger.warning(
                f"Error searching for existing conversation: {e}. Creating new one."
            )

        # No existing conversation found, create new one
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            conversation_id=conversation_id,
            agent_id=agent_id,
            channel=MessageChannel.TELEGRAM,
            external_user_id=external_user_id,
            external_conversation_id=external_conversation_id,
            status=ConversationStatus.AI_ACTIVE,
            marketing_status=MarketingStatus.NEW,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        await self.dynamodb.create_conversation(conversation)
        logger.info(
            f"Created new conversation {conversation_id} for chat {external_user_id}"
        )
        return conversation

    async def send_message(
        self, binding_id: str, chat_id: str, message_text: str
    ) -> dict[str, Any]:
        """Send message via Telegram Bot API."""
        # Get bot token
        bot_token = await self.channel_binding_service.get_access_token(binding_id)

        # Send message via Telegram Bot API
        url = f"{self.TELEGRAM_API_BASE_URL}{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message_text,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)

            if response.status_code != 200:
                error_text = response.text
                logger.error(
                    f"Failed to send Telegram message: {response.status_code} - {error_text}"
                )
                response.raise_for_status()

            result = response.json()

            if not result.get("ok"):
                error_description = result.get("description", "Unknown error")
                logger.error(f"Telegram API error: {error_description}")
                raise ValueError(f"Telegram API error: {error_description}")

            logger.info(f"Sent Telegram message to chat {chat_id}")
            return result

    async def verify_bot_token(self, bot_token: str) -> bool:
        """Verify bot token by calling getMe API."""
        url = f"{self.TELEGRAM_API_BASE_URL}{bot_token}/getMe"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    logger.warning(
                        f"Telegram getMe failed: {response.status_code} - {response.text}"
                    )
                    return False

                result = response.json()

                if result.get("ok") and result.get("result"):
                    bot_info = result["result"]
                    logger.info(
                        f"Telegram bot verified: @{bot_info.get('username', 'N/A')} (id: {bot_info.get('id')})"
                    )
                    return True
                else:
                    logger.warning(f"Telegram getMe returned not ok: {result}")
                    return False

        except httpx.TimeoutException:
            logger.error("Timeout when verifying Telegram bot token")
            return False
        except Exception as e:
            logger.error(f"Error verifying Telegram bot token: {e}", exc_info=True)
            return False

    async def set_webhook(
        self, binding_id: str, webhook_url: str, secret_token: Optional[str] = None
    ) -> bool:
        """Set webhook URL for Telegram bot."""
        bot_token = await self.channel_binding_service.get_access_token(binding_id)
        url = f"{self.TELEGRAM_API_BASE_URL}{bot_token}/setWebhook"

        payload = {"url": webhook_url}
        if secret_token:
            payload["secret_token"] = secret_token

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)

                if response.status_code != 200:
                    logger.error(
                        f"Failed to set Telegram webhook: {response.status_code} - {response.text}"
                    )
                    return False

                result = response.json()

                if result.get("ok"):
                    logger.info(f"Telegram webhook set successfully: {webhook_url}")
                    return True
                else:
                    error_description = result.get("description", "Unknown error")
                    logger.error(f"Telegram setWebhook error: {error_description}")
                    return False

        except Exception as e:
            logger.error(f"Error setting Telegram webhook: {e}", exc_info=True)
            return False
