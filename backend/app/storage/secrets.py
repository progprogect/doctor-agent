"""AWS Secrets Manager client."""

import json
import logging
from functools import lru_cache
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


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
            cached_value = self._cache[secret_name]
            # Ensure cached value is clean (should never be JSON, but check just in case)
            if isinstance(cached_value, str):
                cached_value = cached_value.strip()
                # If cached value is JSON, something went wrong - extract it
                if cached_value.startswith('{') and cached_value.endswith('}'):
                    try:
                        parsed = json.loads(cached_value)
                        if isinstance(parsed, dict):
                            for key in ["api_key", "OPENAI_API_KEY", "openai_api_key", "value"]:
                                if key in parsed and isinstance(parsed[key], str):
                                    cached_value = parsed[key].strip()
                                    break
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing cached JSON: {e}")
                        pass
            return cached_value

        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_value = response["SecretString"]

            # Try to parse as JSON
            try:
                secret_data = json.loads(secret_value)
                # If it's a dict, extract the value by key
                if isinstance(secret_data, dict):
                    # Common pattern: {"api_key": "value"} or {"OPENAI_API_KEY": "value"}
                    for key in ["api_key", "OPENAI_API_KEY", "openai_api_key", "value"]:
                        if key in secret_data:
                            extracted_value = secret_data[key]
                            # Ensure extracted value is a string
                            if isinstance(extracted_value, str):
                                secret_value = extracted_value
                            elif isinstance(extracted_value, dict):
                                # If it's still a dict, something is wrong - try to find string value
                                for v in extracted_value.values():
                                    if isinstance(v, str):
                                        secret_value = v
                                        break
                            break
            except json.JSONDecodeError:
                # Not JSON, use as-is
                pass

            # Clean up whitespace
            secret_value = secret_value.strip().strip('"').strip("'")
            
            # CRITICAL: Validate that we never cache a JSON string
            # If secret_value still looks like JSON after extraction, something went wrong
            if secret_value.startswith('{') and secret_value.endswith('}'):
                # Last attempt: try to extract any string value from the JSON
                try:
                    parsed = json.loads(secret_value)
                    if isinstance(parsed, dict):
                        # Get the first string value we find that looks like an API key
                        for v in parsed.values():
                            if isinstance(v, str) and v.strip().startswith('sk-'):
                                secret_value = v.strip()
                                break
                        # If still JSON, raise error - we should never cache this
                        if secret_value.startswith('{'):
                            logger.error(f"Failed to extract secret value from JSON for {secret_name}")
                            raise ValueError(
                                f"Failed to extract secret value from JSON for {secret_name}. "
                                f"Got JSON string instead of plain value."
                            )
                except (json.JSONDecodeError, ValueError) as e:
                    # If we can't extract or it's still JSON, don't cache it
                    logger.error(f"Error extracting from JSON: {e}")
                    raise ValueError(
                        f"Secret {secret_name} appears to be malformed JSON. "
                        f"Expected plain value or JSON with extractable string value."
                    )

            # Final cleanup
            secret_value = secret_value.strip().strip('"').strip("'")

            # Only cache if it's a clean string (not JSON)
            if use_cache and not (secret_value.startswith('{') and secret_value.endswith('}')):
                self._cache[secret_name] = secret_value

            return secret_value

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise ValueError(f"Secret {secret_name} not found") from e
            raise RuntimeError(f"Failed to retrieve secret {secret_name}: {e}") from e

    async def get_openai_api_key(self) -> str:
        """Get OpenAI API key from Secrets Manager."""
        # Clear cache to ensure fresh retrieval
        self.clear_cache(self.settings.secrets_manager_openai_key_name)
        
        # Get secret - get_secret() already handles JSON extraction
        api_key = await self.get_secret(self.settings.secrets_manager_openai_key_name)
        
        # Final cleanup
        api_key = api_key.strip().strip('"').strip("'")
        
        # Validate that it looks like an API key (starts with sk-)
        if not api_key.startswith('sk-'):
            logger.error(f"Invalid API key format! First 50 chars: {repr(api_key[:50])}")
            raise ValueError(
                f"Invalid API key format: key does not start with 'sk-'. "
                f"Got: {api_key[:50]}..." if len(api_key) > 50 else f"Got: {api_key}"
            )
        
        return api_key

    def clear_cache(self, secret_name: Optional[str] = None) -> None:
        """Clear cached secrets."""
        if secret_name:
            self._cache.pop(secret_name, None)
        else:
            self._cache.clear()

    async def create_channel_token_secret(
        self,
        binding_id: str,
        channel_type: str,
        access_token: str,
        metadata: dict,
    ) -> str:
        """Create secret for channel access token."""
        secret_name = f"doctor-agent/channels/{channel_type}/{binding_id}/access-token"
        secret_value = json.dumps(
            {
                "access_token": access_token,
                **metadata,
            }
        )

        try:
            self.client.create_secret(
                Name=secret_name,
                SecretString=secret_value,
                Description=f"Access token for {channel_type} channel binding {binding_id}",
            )
            logger.info(f"Created channel token secret: {secret_name}")
            return secret_name
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceExistsException":
                # Secret already exists, update it instead
                logger.warning(f"Secret {secret_name} already exists, updating...")
                self.client.update_secret(
                    SecretId=secret_name,
                    SecretString=secret_value,
                )
                return secret_name
            raise RuntimeError(f"Failed to create channel token secret: {e}") from e

    async def get_channel_token(self, secret_name: str) -> str:
        """Get channel access token from secret."""
        try:
            # Get secret directly from AWS Secrets Manager to avoid get_secret's JSON extraction logic
            # Channel tokens are stored as {"access_token": "...", **metadata}
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_value = response["SecretString"]
            
            # Try to parse as JSON (channel tokens are stored as JSON)
            try:
                data = json.loads(secret_value)
                if isinstance(data, dict):
                    # Extract access_token from JSON
                    access_token = data.get("access_token")
                    if access_token and isinstance(access_token, str):
                        return access_token.strip()
                    # If access_token not found, try to return the whole value as string
                    logger.warning(f"access_token not found in secret {secret_name}, returning first string value")
                    for v in data.values():
                        if isinstance(v, str):
                            return v.strip()
            except json.JSONDecodeError:
                # Not JSON, return as-is (for backward compatibility with plain token storage)
                pass
            
            # If not JSON or access_token not found, return as-is
            return secret_value.strip()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise ValueError(f"Secret {secret_name} not found") from e
            raise RuntimeError(f"Failed to retrieve channel token from {secret_name}: {e}") from e
        except Exception as e:
            logger.error(f"Failed to get channel token from {secret_name}: {e}")
            raise ValueError(f"Failed to get channel token from {secret_name}: {e}") from e

    async def update_channel_token(
        self,
        secret_name: str,
        access_token: str,
        metadata: dict,
    ) -> None:
        """Update channel token in secret."""
        secret_value = json.dumps(
            {
                "access_token": access_token,
                **metadata,
            }
        )
        try:
            self.client.update_secret(
                SecretId=secret_name,
                SecretString=secret_value,
            )
            # Clear cache for this secret
            self.clear_cache(secret_name)
            logger.info(f"Updated channel token secret: {secret_name}")
        except ClientError as e:
            raise RuntimeError(f"Failed to update channel token secret: {e}") from e

    async def delete_channel_token_secret(self, secret_name: str) -> None:
        """Delete channel token secret."""
        try:
            self.client.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=True,
            )
            # Clear cache for this secret
            self.clear_cache(secret_name)
            logger.info(f"Deleted channel token secret: {secret_name}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                # Secret doesn't exist, that's fine
                logger.warning(f"Secret {secret_name} not found, skipping deletion")
                return
            raise RuntimeError(f"Failed to delete channel token secret: {e}") from e


@lru_cache()
def get_secrets_manager() -> SecretsManager:
    """Get cached Secrets Manager instance."""
    settings = get_settings()
    return SecretsManager(settings)




