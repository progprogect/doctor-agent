"""AWS Secrets Manager client."""

import json
from functools import lru_cache
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config import Settings, get_settings


class SecretsManager:
    """AWS Secrets Manager client wrapper."""

    def __init__(self, settings: Settings):
        """Initialize Secrets Manager client."""
        self.settings = settings
        self.client = boto3.client(
            "secretsmanager",
            region_name=settings.secrets_manager_region or settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self._cache: dict[str, str] = {}

    async def get_secret(self, secret_name: str, use_cache: bool = True) -> str:
        """Get secret value from Secrets Manager."""
        if use_cache and secret_name in self._cache:
            return self._cache[secret_name]

        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_value = response["SecretString"]

            # Try to parse as JSON
            try:
                secret_data = json.loads(secret_value)
                # If it's a dict, try to get the value by key or return the whole dict as string
                if isinstance(secret_data, dict):
                    # Common pattern: {"api_key": "value"} or {"OPENAI_API_KEY": "value"}
                    for key in ["api_key", "OPENAI_API_KEY", "openai_api_key", "value"]:
                        if key in secret_data:
                            secret_value = secret_data[key]
                            break
            except json.JSONDecodeError:
                # Not JSON, use as-is
                pass

            if use_cache:
                self._cache[secret_name] = secret_value

            return secret_value

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise ValueError(f"Secret {secret_name} not found") from e
            raise RuntimeError(f"Failed to retrieve secret {secret_name}: {e}") from e

    async def get_openai_api_key(self) -> str:
        """Get OpenAI API key from Secrets Manager."""
        return await self.get_secret(self.settings.secrets_manager_openai_key_name)

    def clear_cache(self, secret_name: Optional[str] = None) -> None:
        """Clear cached secrets."""
        if secret_name:
            self._cache.pop(secret_name, None)
        else:
            self._cache.clear()


@lru_cache()
def get_secrets_manager() -> SecretsManager:
    """Get cached Secrets Manager instance."""
    settings = get_settings()
    return SecretsManager(settings)

