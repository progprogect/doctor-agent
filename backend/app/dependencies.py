"""Dependency injection for FastAPI."""

from typing import Union

from fastapi import Depends

from app.config import Settings, get_settings
from app.storage.dynamodb import DynamoDBClient, get_dynamodb_client
from app.storage.dynamodb_cache import DynamoDBCacheClient, get_dynamodb_cache_client
from app.storage.postgres import PostgreSQLClient, get_postgres_client
from app.storage.postgres_cache import PostgresCacheClient, get_postgres_cache_client
from app.storage.secrets import SecretsManager, get_secrets_manager
from app.storage.postgres_secrets import PostgresSecretsManager, get_postgres_secrets_manager
from app.services.llm_factory import LLMFactory, get_llm_factory
from app.services.moderation_service import ModerationService, get_moderation_service


def get_config() -> Settings:
    """Get application settings."""
    return get_settings()


def _use_postgres() -> bool:
    return get_settings().database_backend == "postgres"


# Storage dependencies
def get_dynamodb() -> Union[DynamoDBClient, PostgreSQLClient]:
    """Get database client (PostgreSQL or DynamoDB based on config)."""
    if _use_postgres():
        return get_postgres_client()
    return get_dynamodb_client()


def get_cache() -> Union[DynamoDBCacheClient, PostgresCacheClient]:
    """Get cache client."""
    if _use_postgres():
        return get_postgres_cache_client()
    return get_dynamodb_cache_client()


def get_secrets() -> Union[SecretsManager, PostgresSecretsManager]:
    """Get secrets manager."""
    if _use_postgres():
        return get_postgres_secrets_manager()
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
        dynamodb: Union[DynamoDBClient, PostgreSQLClient] = Depends(get_dynamodb),
        cache: Union[DynamoDBCacheClient, PostgresCacheClient] = Depends(get_cache),
    ):
        self.config = config
        self.dynamodb = dynamodb
        self.cache = cache

