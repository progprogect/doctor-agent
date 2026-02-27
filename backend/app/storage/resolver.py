"""Resolve storage clients based on database_backend config."""

from app.config import get_settings
from app.storage.secrets import get_secrets_manager as get_aws_secrets_manager
from app.storage.postgres_secrets import get_postgres_secrets_manager


def get_secrets_manager():
    """Get secrets manager (AWS or PostgreSQL based on config)."""
    if get_settings().database_backend == "postgres":
        return get_postgres_secrets_manager()
    return get_aws_secrets_manager()
