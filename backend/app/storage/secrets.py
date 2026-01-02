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
            cached_value = self._cache[secret_name]
            # Ensure cached value is also cleaned
            if isinstance(cached_value, str):
                cached_value = cached_value.strip().strip('"').strip("'")
                if cached_value.startswith('{') and cached_value.endswith('}'):
                    try:
                        parsed = json.loads(cached_value)
                        if isinstance(parsed, dict):
                            for key in ["api_key", "OPENAI_API_KEY", "openai_api_key", "value"]:
                                if key in parsed:
                                    cached_value = parsed[key]
                                    break
                    except json.JSONDecodeError:
                        pass
                cached_value = cached_value.strip().strip('"').strip("'")
            return cached_value

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
                            # If the extracted value is still a dict or looks like JSON, continue processing
                            if isinstance(secret_value, dict):
                                # Convert dict back to string for further processing
                                secret_value = json.dumps(secret_value)
                            break
            except json.JSONDecodeError:
                # Not JSON, use as-is
                pass

            # Clean up the secret value - remove any extra whitespace, quotes, or JSON artifacts
            # Keep processing until we get a clean string that doesn't look like JSON
            max_iterations = 5
            iteration = 0
            while iteration < max_iterations:
                secret_value = secret_value.strip().strip('"').strip("'")
                
                # If it still looks like JSON (starts with {), try parsing again
                if secret_value.startswith('{') and secret_value.endswith('}'):
                    try:
                        parsed = json.loads(secret_value)
                        if isinstance(parsed, dict):
                            found = False
                            for key in ["api_key", "OPENAI_API_KEY", "openai_api_key", "value"]:
                                if key in parsed:
                                    secret_value = parsed[key]
                                    # If extracted value is still a dict, convert to string
                                    if isinstance(secret_value, dict):
                                        secret_value = json.dumps(secret_value)
                                    found = True
                                    break
                            if not found:
                                # No matching key found, break to avoid infinite loop
                                break
                        else:
                            # Not a dict, break
                            break
                    except json.JSONDecodeError:
                        # Can't parse, break
                        break
                else:
                    # Doesn't look like JSON, we're done
                    break
                
                iteration += 1

            # Final cleanup
            secret_value = secret_value.strip().strip('"').strip("'")
            
            # Validate: if it still looks like JSON after all processing, something is wrong
            if secret_value.startswith('{') and secret_value.endswith('}'):
                # Last attempt: try to extract any string value from the JSON
                try:
                    parsed = json.loads(secret_value)
                    if isinstance(parsed, dict):
                        # Get the first string value we find
                        for v in parsed.values():
                            if isinstance(v, str) and v.startswith('sk-'):
                                secret_value = v
                                break
                except:
                    pass

            # Final cleanup again
            secret_value = secret_value.strip().strip('"').strip("'")

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
        # Clear cache to ensure fresh retrieval
        self.clear_cache(self.settings.secrets_manager_openai_key_name)
        
        api_key = await self.get_secret(self.settings.secrets_manager_openai_key_name)
        
        # Clean up the API key - remove any extra whitespace, quotes, or JSON artifacts
        api_key = api_key.strip().strip('"').strip("'")
        
        # Remove JSON-like artifacts if present (e.g., {"OPENAI_API_KEY": "value"} -> value)
        if api_key.startswith('{') and api_key.endswith('}'):
            try:
                parsed = json.loads(api_key)
                if isinstance(parsed, dict):
                    for key in ["OPENAI_API_KEY", "openai_api_key", "api_key", "value"]:
                        if key in parsed:
                            api_key = parsed[key]
                            break
            except json.JSONDecodeError:
                pass
        
        # Final cleanup
        api_key = api_key.strip().strip('"').strip("'")
        
        # Validate that it looks like an API key (starts with sk-)
        if not api_key.startswith('sk-'):
            raise ValueError(f"Invalid API key format: key does not start with 'sk-'")
        
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




