"""Dependency injection for FastAPI."""

from fastapi import Depends

from app.config import Settings, get_settings
from app.storage.dynamodb import DynamoDBClient, get_dynamodb_client
from app.storage.opensearch import OpenSearchClient, get_opensearch_client
from app.storage.redis import RedisClient, get_redis_client
from app.storage.secrets import SecretsManager, get_secrets_manager
from app.services.llm_factory import LLMFactory, get_llm_factory
from app.services.moderation_service import ModerationService, get_moderation_service


def get_config() -> Settings:
    """Get application settings."""
    return get_settings()


# Storage dependencies
def get_dynamodb() -> DynamoDBClient:
    """Get DynamoDB client."""
    return get_dynamodb_client()


def get_opensearch() -> OpenSearchClient:
    """Get OpenSearch client."""
    return get_opensearch_client()


def get_redis() -> RedisClient:
    """Get Redis client."""
    return get_redis_client()


def get_secrets() -> SecretsManager:
    """Get Secrets Manager client."""
    return get_secrets_manager()


# Service dependencies
def get_llm_factory_dep() -> LLMFactory:
    """Get LLM factory."""
    return get_llm_factory()


def get_moderation_service_dep() -> ModerationService:
    """Get moderation service."""
    return get_moderation_service()


# Common dependency combinations
class CommonDependencies:
    """Common dependencies for endpoints."""

    def __init__(
        self,
        config: Settings = Depends(get_config),
        dynamodb: DynamoDBClient = Depends(get_dynamodb),
        redis: RedisClient = Depends(get_redis),
    ):
        self.config = config
        self.dynamodb = dynamodb
        self.redis = redis

