"""DynamoDB client wrapper."""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.models.channel_binding import ChannelBinding
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageRole

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """DynamoDB client wrapper."""

    def __init__(self, settings: Settings):
        """Initialize DynamoDB client."""
        self.settings = settings
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.aws_region,
            endpoint_url=settings.dynamodb_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.tables = {
            "conversations": self.dynamodb.Table(settings.dynamodb_table_conversations),
            "messages": self.dynamodb.Table(settings.dynamodb_table_messages),
            "agents": self.dynamodb.Table(settings.dynamodb_table_agents),
            "audit_logs": self.dynamodb.Table(settings.dynamodb_table_audit_logs),
            "channel_bindings": self.dynamodb.Table(settings.dynamodb_table_channel_bindings),
        }
        self.message_ttl_seconds = settings.message_ttl_hours * 3600

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Recursively convert float values to Decimal for DynamoDB compatibility."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        else:
            return obj

    def _calculate_ttl(self, base_time: datetime) -> int:
        """Calculate TTL timestamp (Unix epoch seconds)."""
        expiry_time = base_time + timedelta(seconds=self.message_ttl_seconds)
        return int(expiry_time.timestamp())

    # Conversation operations
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        item = conversation.model_dump(exclude_none=True)
        # Convert datetime objects to ISO format strings for DynamoDB
        if "created_at" in item and isinstance(item["created_at"], datetime):
            item["created_at"] = item["created_at"].isoformat()
        if "updated_at" in item and isinstance(item["updated_at"], datetime):
            item["updated_at"] = item["updated_at"].isoformat()
        item["ttl"] = self._calculate_ttl(conversation.created_at)

        self.tables["conversations"].put_item(Item=item)
        return conversation

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        response = self.tables["conversations"].get_item(
            Key={"conversation_id": conversation_id}
        )
        item = response.get("Item")
        if not item:
            return None
        return Conversation(**item)

    async def update_conversation(
        self,
        conversation_id: str,
        status: Optional[ConversationStatus] = None,
        handoff_reason: Optional[str] = None,
        request_type: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[Conversation]:
        """Update conversation."""
        # Get old conversation to check status change
        old_conversation = await self.get_conversation(conversation_id)
        old_status = None
        if old_conversation:
            old_status = (
                old_conversation.status.value
                if hasattr(old_conversation.status, "value")
                else str(old_conversation.status)
            )

        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}

        if status:
            update_expression_parts.append("#status = :status")
            expression_attribute_names["#status"] = "status"
            expression_attribute_values[":status"] = status.value

        if handoff_reason is not None:
            update_expression_parts.append("handoff_reason = :handoff_reason")
            expression_attribute_values[":handoff_reason"] = handoff_reason

        if request_type is not None:
            update_expression_parts.append("request_type = :request_type")
            expression_attribute_values[":request_type"] = request_type

        for key, value in kwargs.items():
            update_expression_parts.append(f"{key} = :{key}")
            expression_attribute_values[f":{key}"] = value

        if not update_expression_parts:
            return await self.get_conversation(conversation_id)

        update_expression_parts.append("updated_at = :updated_at")
        expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()

        try:
            self.tables["conversations"].update_item(
                Key={"conversation_id": conversation_id},
                UpdateExpression=f"SET {', '.join(update_expression_parts)}",
                ExpressionAttributeValues=expression_attribute_values,
                ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
                ReturnValues="ALL_NEW",
            )
            updated_conversation = await self.get_conversation(conversation_id)
            
            # Broadcast update to admin dashboard
            if updated_conversation:
                try:
                    from app.api.admin_websocket import get_admin_broadcast_manager
                    from app.models.conversation import ConversationStatus
                    
                    broadcast_manager = get_admin_broadcast_manager()
                    new_status = (
                        updated_conversation.status.value
                        if hasattr(updated_conversation.status, "value")
                        else str(updated_conversation.status)
                    )
                    
                    # Check if this is a new escalation (status changed to NEEDS_HUMAN)
                    if (
                        status
                        and status == ConversationStatus.NEEDS_HUMAN
                        and (old_status is None or old_status != ConversationStatus.NEEDS_HUMAN.value)
                    ):
                        await broadcast_manager.broadcast_new_escalation(
                            updated_conversation, handoff_reason
                        )
                    else:
                        # Regular status update
                        await broadcast_manager.broadcast_conversation_update(
                            updated_conversation
                        )
                except Exception as e:
                    # Don't fail the update if broadcast fails
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Failed to broadcast conversation update: {e}",
                        exc_info=True,
                    )
            
            return updated_conversation
        except ClientError as e:
            raise RuntimeError(f"Failed to update conversation: {e}") from e

    async def list_conversations(
        self,
        agent_id: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        limit: int = 100,
    ) -> list[Conversation]:
        """List conversations with optional filters."""
        # For MVP, using scan (not efficient for large datasets)
        # In production, use GSI for agent_id and status
        filter_expression = None
        expression_attribute_values = {}
        expression_attribute_names = {}

        if agent_id:
            filter_expression = "agent_id = :agent_id"
            expression_attribute_values[":agent_id"] = agent_id

        if status:
            # Use ExpressionAttributeNames for reserved keywords like "status"
            status_filter = "#status = :status"
            expression_attribute_names["#status"] = "status"
            if filter_expression:
                filter_expression += " AND " + status_filter
            else:
                filter_expression = status_filter
            expression_attribute_values[":status"] = status.value

        scan_kwargs = {"Limit": limit}
        if filter_expression:
            scan_kwargs["FilterExpression"] = filter_expression
            scan_kwargs["ExpressionAttributeValues"] = expression_attribute_values
            if expression_attribute_names:
                scan_kwargs["ExpressionAttributeNames"] = expression_attribute_names

        response = self.tables["conversations"].scan(**scan_kwargs)
        items = response.get("Items", [])
        return [Conversation(**item) for item in items]

    # Message operations
    async def create_message(self, message: Message) -> Message:
        """Create a new message."""
        item = message.model_dump(exclude_none=True)
        # Convert datetime objects to ISO format strings for DynamoDB
        if "timestamp" in item and isinstance(item["timestamp"], datetime):
            item["timestamp"] = item["timestamp"].isoformat()
        item["ttl"] = self._calculate_ttl(message.timestamp)

        self.tables["messages"].put_item(Item=item)
        return message

    async def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID."""
        response = self.tables["messages"].get_item(Key={"message_id": message_id})
        item = response.get("Item")
        if not item:
            return None
        return Message(**item)

    async def list_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        reverse: bool = True,
    ) -> list[Message]:
        """List messages for a conversation."""
        # For MVP, using query on conversation_id (requires GSI)
        # Fallback to scan if GSI not available
        try:
            response = self.tables["messages"].query(
                IndexName="conversation_id-index",  # Requires GSI
                KeyConditionExpression="conversation_id = :conv_id",
                ExpressionAttributeValues={":conv_id": conversation_id},
                Limit=limit,
                ScanIndexForward=not reverse,
            )
            items = response.get("Items", [])
        except ClientError:
            # Fallback to scan if GSI doesn't exist
            response = self.tables["messages"].scan(
                FilterExpression="conversation_id = :conv_id",
                ExpressionAttributeValues={":conv_id": conversation_id},
                Limit=limit,
            )
            items = response.get("Items", [])
            # Sort by timestamp
            items.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse)

        return [Message(**item) for item in items]

    # Agent operations
    async def create_agent(self, agent_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """Create or update agent configuration."""
        # Convert float values to Decimal for DynamoDB compatibility
        config_converted = self._convert_floats_to_decimal(config)
        
        item = {
            "agent_id": agent_id,
            "config": config_converted,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }
        self.tables["agents"].put_item(Item=item)
        return item

    async def get_agent(self, agent_id: str) -> Optional[dict[str, Any]]:
        """Get agent configuration."""
        response = self.tables["agents"].get_item(Key={"agent_id": agent_id})
        item = response.get("Item")
        return item

    async def update_agent_status(
        self, 
        agent_id: str, 
        is_active: bool
    ) -> Optional[dict[str, Any]]:
        """Update agent is_active status atomically."""
        try:
            response = self.tables["agents"].update_item(
                Key={"agent_id": agent_id},
                UpdateExpression="SET is_active = :active, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ":active": is_active,
                    ":updated_at": datetime.utcnow().isoformat(),
                },
                ReturnValues="ALL_NEW",
                ConditionExpression="attribute_exists(agent_id)",
            )
            return response.get("Attributes")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None  # Agent doesn't exist
            raise RuntimeError(f"Failed to update agent status: {e}") from e

    async def list_agents(self, active_only: bool = True) -> list[dict[str, Any]]:
        """List all agents."""
        if active_only:
            response = self.tables["agents"].scan(
                FilterExpression="is_active = :active",
                ExpressionAttributeValues={":active": True},
            )
        else:
            response = self.tables["agents"].scan()
        return response.get("Items", [])

    # Channel binding operations
    async def create_channel_binding(self, binding: ChannelBinding) -> ChannelBinding:
        """Create a new channel binding."""
        item = binding.model_dump(exclude_none=True)
        # Convert datetime objects to ISO format strings for DynamoDB
        if "created_at" in item and isinstance(item["created_at"], datetime):
            item["created_at"] = item["created_at"].isoformat()
        if "updated_at" in item and isinstance(item["updated_at"], datetime):
            item["updated_at"] = item["updated_at"].isoformat()
        # Convert enum to string
        if "channel_type" in item:
            item["channel_type"] = (
                item["channel_type"].value
                if hasattr(item["channel_type"], "value")
                else str(item["channel_type"])
            )

        self.tables["channel_bindings"].put_item(Item=item)
        return binding

    async def get_channel_binding(self, binding_id: str) -> Optional[ChannelBinding]:
        """Get channel binding by ID."""
        response = self.tables["channel_bindings"].get_item(
            Key={"binding_id": binding_id}
        )
        item = response.get("Item")
        if not item:
            return None
        return ChannelBinding(**item)

    async def get_channel_bindings_by_agent(
        self,
        agent_id: str,
        channel_type: Optional[str] = None,
        active_only: bool = True,
    ) -> list[ChannelBinding]:
        """Get channel bindings for an agent."""
        try:
            # Use GSI if available
            # agent_id-index has agent_id as hash key and channel_type as range key
            key_condition = "agent_id = :agent_id"
            expression_attribute_values = {":agent_id": agent_id}
            expression_attribute_names = {}
            filter_expressions = []
            
            # channel_type is range key in GSI, so it can be in KeyConditionExpression
            if channel_type:
                key_condition += " AND channel_type = :channel_type"
                expression_attribute_values[":channel_type"] = channel_type

            if active_only:
                # Use ExpressionAttributeNames for reserved keyword "is_active"
                expression_attribute_names["#is_active"] = "is_active"
                filter_expressions.append("#is_active = :is_active")
                expression_attribute_values[":is_active"] = True

            query_kwargs = {
                "IndexName": "agent_id-index",
                "KeyConditionExpression": key_condition,
                "ExpressionAttributeValues": expression_attribute_values,
            }
            
            if filter_expressions:
                query_kwargs["FilterExpression"] = " AND ".join(filter_expressions)
            
            # Only include ExpressionAttributeNames if we have attribute names
            if expression_attribute_names:
                query_kwargs["ExpressionAttributeNames"] = expression_attribute_names

            response = self.tables["channel_bindings"].query(**query_kwargs)
            items = response.get("Items", [])
        except ClientError:
            # Fallback to scan if GSI doesn't exist
            filter_expression = "agent_id = :agent_id"
            expression_attribute_values = {":agent_id": agent_id}

            if channel_type:
                filter_expression += " AND channel_type = :channel_type"
                expression_attribute_values[":channel_type"] = channel_type

            if active_only:
                filter_expression += " AND is_active = :active"
                expression_attribute_values[":active"] = True

            response = self.tables["channel_bindings"].scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_attribute_values,
            )
            items = response.get("Items", [])

        # Filter by active_only if needed (when using scan)
        if active_only and not channel_type:
            items = [item for item in items if item.get("is_active", True)]

        return [ChannelBinding(**item) for item in items]

    async def get_channel_binding_by_account_id(
        self, channel_type: str, account_id: str
    ) -> Optional[ChannelBinding]:
        """Get channel binding by channel account ID."""
        try:
            # Use GSI if available
            response = self.tables["channel_bindings"].query(
                IndexName="channel_account-index",
                KeyConditionExpression="channel_type = :channel_type AND channel_account_id = :account_id",
                ExpressionAttributeValues={
                    ":channel_type": channel_type,
                    ":account_id": account_id,
                },
            )
            items = response.get("Items", [])
            if not items:
                return None
            # Return first active binding if multiple exist
            active_bindings = [item for item in items if item.get("is_active", True)]
            if active_bindings:
                return ChannelBinding(**active_bindings[0])
            # Return first binding if no active ones
            return ChannelBinding(**items[0])
        except ClientError:
            # Fallback to scan if GSI doesn't exist
            response = self.tables["channel_bindings"].scan(
                FilterExpression="channel_type = :channel_type AND channel_account_id = :account_id",
                ExpressionAttributeValues={
                    ":channel_type": channel_type,
                    ":account_id": account_id,
                },
            )
            items = response.get("Items", [])
            if not items:
                return None
            # Return first active binding if multiple exist
            active_bindings = [item for item in items if item.get("is_active", True)]
            if active_bindings:
                return ChannelBinding(**active_bindings[0])
            return ChannelBinding(**items[0])

    async def update_channel_binding(
        self, binding_id: str, **kwargs: Any
    ) -> Optional[ChannelBinding]:
        """Update channel binding."""
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}

        for key, value in kwargs.items():
            if key == "channel_type" and hasattr(value, "value"):
                value = value.value
            update_expression_parts.append(f"{key} = :{key}")
            expression_attribute_values[f":{key}"] = value

        if not update_expression_parts:
            return await self.get_channel_binding(binding_id)

        update_expression_parts.append("updated_at = :updated_at")
        expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()

        try:
            self.tables["channel_bindings"].update_item(
                Key={"binding_id": binding_id},
                UpdateExpression=f"SET {', '.join(update_expression_parts)}",
                ExpressionAttributeValues=expression_attribute_values,
                ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
                ReturnValues="ALL_NEW",
            )
            return await self.get_channel_binding(binding_id)
        except ClientError as e:
            logger.error(f"Failed to update channel binding: {e}")
            return None

    async def delete_channel_binding(self, binding_id: str) -> None:
        """Delete channel binding."""
        self.tables["channel_bindings"].delete_item(Key={"binding_id": binding_id})

    # Audit log operations
    async def create_audit_log(
        self,
        admin_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Create audit log entry."""
        log_id = f"{resource_type}_{resource_id}_{int(time.time())}"
        item = {
            "log_id": log_id,
            "admin_id": admin_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.tables["audit_logs"].put_item(Item=item)
        return item

    async def list_audit_logs(
        self,
        admin_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List audit logs."""
        filter_expression = None
        expression_attribute_values = {}

        if admin_id:
            filter_expression = "admin_id = :admin_id"
            expression_attribute_values[":admin_id"] = admin_id

        if resource_type:
            resource_filter = "resource_type = :resource_type"
            if filter_expression:
                filter_expression += " AND " + resource_filter
            else:
                filter_expression = resource_filter
            expression_attribute_values[":resource_type"] = resource_type

        scan_kwargs = {"Limit": limit}
        if filter_expression:
            scan_kwargs["FilterExpression"] = filter_expression
            scan_kwargs["ExpressionAttributeValues"] = expression_attribute_values

        response = self.tables["audit_logs"].scan(**scan_kwargs)
        return response.get("Items", [])


@lru_cache()
def get_dynamodb_client() -> DynamoDBClient:
    """Get cached DynamoDB client instance."""
    settings = get_settings()
    return DynamoDBClient(settings)




