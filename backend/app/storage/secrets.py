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
            logger.info(f"[SECRETS] Found cached value for {secret_name} (first 50 chars): {repr(cached_value[:50]) if len(cached_value) > 50 else repr(cached_value)}")
            # Ensure cached value is clean (should never be JSON, but check just in case)
            if isinstance(cached_value, str):
                cached_value = cached_value.strip()
                # If cached value is JSON, something went wrong - extract it
                if cached_value.startswith('{') and cached_value.endswith('}'):
                    logger.warning(f"[SECRETS] Cached value is JSON! Extracting...")
                    try:
                        parsed = json.loads(cached_value)
                        if isinstance(parsed, dict):
                            for key in ["api_key", "OPENAI_API_KEY", "openai_api_key", "value"]:
                                if key in parsed and isinstance(parsed[key], str):
                                    cached_value = parsed[key].strip()
                                    logger.info(f"[SECRETS] Extracted from cached JSON using key '{key}': {repr(cached_value[:20])}...")
                                    break
                    except json.JSONDecodeError as e:
                        logger.error(f"[SECRETS] Error parsing cached JSON: {e}")
                        pass
            logger.info(f"[SECRETS] Returning cached value (first 20 chars): {repr(cached_value[:20]) if len(cached_value) > 20 else repr(cached_value)}, starts_with_sk: {cached_value.startswith('sk-') if isinstance(cached_value, str) else False}, starts_with_brace: {cached_value.startswith('{') if isinstance(cached_value, str) else False}")
            return cached_value

        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_value = response["SecretString"]
            logger.info(f"[SECRETS] Raw secret_value from AWS (first 50 chars): {repr(secret_value[:50]) if len(secret_value) > 50 else repr(secret_value)}")

            # Try to parse as JSON
            try:
                secret_data = json.loads(secret_value)
                logger.info(f"[SECRETS] Parsed as JSON, type: {type(secret_data)}, keys: {list(secret_data.keys()) if isinstance(secret_data, dict) else 'N/A'}")
                # If it's a dict, extract the value by key
                if isinstance(secret_data, dict):
                    # Common pattern: {"api_key": "value"} or {"OPENAI_API_KEY": "value"}
                    for key in ["api_key", "OPENAI_API_KEY", "openai_api_key", "value"]:
                        if key in secret_data:
                            extracted_value = secret_data[key]
                            logger.info(f"[SECRETS] Found key '{key}', extracted_value type: {type(extracted_value)}, value (first 20 chars): {repr(str(extracted_value)[:20]) if len(str(extracted_value)) > 20 else repr(extracted_value)}")
                            # Ensure extracted value is a string
                            if isinstance(extracted_value, str):
                                secret_value = extracted_value
                                logger.info(f"[SECRETS] Assigned extracted_value to secret_value: {repr(secret_value[:20])}...")
                            elif isinstance(extracted_value, dict):
                                # If it's still a dict, something is wrong - try to find string value
                                for v in extracted_value.values():
                                    if isinstance(v, str):
                                        secret_value = v
                                        break
                            break
            except json.JSONDecodeError:
                # Not JSON, use as-is
                logger.debug(f"[SECRETS] Not JSON, using as-is")
                pass

            # Clean up whitespace
            secret_value = secret_value.strip().strip('"').strip("'")
            logger.info(f"[SECRETS] After cleanup, secret_value (first 20 chars): {repr(secret_value[:20]) if len(secret_value) > 20 else repr(secret_value)}")
            
            # CRITICAL: Validate that we never cache a JSON string
            # If secret_value still looks like JSON after extraction, something went wrong
            if secret_value.startswith('{') and secret_value.endswith('}'):
                logger.warning(f"[SECRETS] secret_value still looks like JSON after extraction! Attempting fallback extraction...")
                # Last attempt: try to extract any string value from the JSON
                try:
                    parsed = json.loads(secret_value)
                    if isinstance(parsed, dict):
                        # Get the first string value we find that looks like an API key
                        for v in parsed.values():
                            if isinstance(v, str) and v.strip().startswith('sk-'):
                                secret_value = v.strip()
                                logger.info(f"[SECRETS] Fallback extraction successful: {repr(secret_value[:20])}...")
                                break
                        # If still JSON, raise error - we should never cache this
                        if secret_value.startswith('{'):
                            logger.error(f"[SECRETS] Failed to extract secret value from JSON for {secret_name}")
                            raise ValueError(
                                f"Failed to extract secret value from JSON for {secret_name}. "
                                f"Got JSON string instead of plain value."
                            )
                except (json.JSONDecodeError, ValueError) as e:
                    # If we can't extract or it's still JSON, don't cache it
                    logger.error(f"[SECRETS] Error extracting from JSON: {e}")
                    raise ValueError(
                        f"Secret {secret_name} appears to be malformed JSON. "
                        f"Expected plain value or JSON with extractable string value."
                    )

            # Final cleanup
            secret_value = secret_value.strip().strip('"').strip("'")
            logger.info(f"[SECRETS] Final secret_value (first 20 chars): {repr(secret_value[:20]) if len(secret_value) > 20 else repr(secret_value)}, starts_with_sk: {secret_value.startswith('sk-')}, starts_with_brace: {secret_value.startswith('{')}")

            # Only cache if it's a clean string (not JSON)
            if use_cache and not (secret_value.startswith('{') and secret_value.endswith('}')):
                self._cache[secret_name] = secret_value
                logger.info(f"[SECRETS] Cached secret_value for {secret_name}")
            else:
                logger.warning(f"[SECRETS] NOT caching secret_value for {secret_name} (looks like JSON: {secret_value.startswith('{')})")

            return secret_value

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise ValueError(f"Secret {secret_name} not found") from e
            raise RuntimeError(f"Failed to retrieve secret {secret_name}: {e}") from e

    async def get_openai_api_key(self) -> str:
        """Get OpenAI API key from Secrets Manager."""
        logger.info(f"[SECRETS] get_openai_api_key() called, clearing cache...")
        # Clear cache to ensure fresh retrieval
        self.clear_cache(self.settings.secrets_manager_openai_key_name)
        
        # Get secret - get_secret() already handles JSON extraction
        api_key = await self.get_secret(self.settings.secrets_manager_openai_key_name)
        logger.info(f"[SECRETS] get_openai_api_key() received from get_secret() (first 20 chars): {repr(api_key[:20]) if len(api_key) > 20 else repr(api_key)}")
        
        # Final cleanup
        api_key = api_key.strip().strip('"').strip("'")
        logger.info(f"[SECRETS] get_openai_api_key() after cleanup (first 20 chars): {repr(api_key[:20]) if len(api_key) > 20 else repr(api_key)}, starts_with_sk: {api_key.startswith('sk-')}")
        
        # Validate that it looks like an API key (starts with sk-)
        if not api_key.startswith('sk-'):
            logger.error(f"[SECRETS] Invalid API key format! Starts with sk-: {api_key.startswith('sk-')}, First 50 chars: {repr(api_key[:50])}")
            raise ValueError(
                f"Invalid API key format: key does not start with 'sk-'. "
                f"Got: {api_key[:50]}..." if len(api_key) > 50 else f"Got: {api_key}"
            )
        
        logger.info(f"[SECRETS] get_openai_api_key() returning valid key (first 10 chars): {repr(api_key[:10])}...")
        return api_key

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




