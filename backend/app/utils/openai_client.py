"""OpenAI client wrapper with retry logic."""

import logging
from functools import lru_cache
from typing import Optional

from openai import AsyncOpenAI, OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import Settings, get_settings
from app.storage.secrets import SecretsManager, get_secrets_manager
from app.utils.model_params import requires_max_completion_tokens

logger = logging.getLogger(__name__)


class OpenAIClientWrapper:
    """OpenAI client wrapper with retry and error handling."""

    def __init__(self, api_key: str, settings: Settings):
        """Initialize OpenAI client."""
        # Ensure API key is clean (no JSON artifacts)
        api_key = api_key.strip().strip('"').strip("'")
        if api_key.startswith('{') and api_key.endswith('}'):
            try:
                import json
                parsed = json.loads(api_key)
                if isinstance(parsed, dict):
                    for key in ["OPENAI_API_KEY", "openai_api_key", "api_key", "value"]:
                        if key in parsed:
                            api_key = parsed[key]
                            break
            except Exception as e:
                logger.error(f"Error extracting from JSON in __init__: {e}")
                pass
        api_key = api_key.strip().strip('"').strip("'")
        self.api_key = api_key
        self.settings = settings
        self._async_client: Optional[AsyncOpenAI] = None
        self._sync_client: Optional[OpenAI] = None

    @property
    def async_client(self) -> AsyncOpenAI:
        """Get async OpenAI client."""
        if self._async_client is None:
            # Ensure api_key is a clean string, not JSON
            api_key = self.api_key
            if isinstance(api_key, str):
                api_key = api_key.strip().strip('"').strip("'")
                # If it looks like JSON, try to extract the actual key
                if api_key.startswith('{') and api_key.endswith('}'):
                    try:
                        import json
                        parsed = json.loads(api_key)
                        if isinstance(parsed, dict):
                            for key in ["OPENAI_API_KEY", "openai_api_key", "api_key", "value"]:
                                if key in parsed and isinstance(parsed[key], str):
                                    api_key = parsed[key]
                                    break
                    except Exception as e:
                        logger.error(f"Error extracting from JSON in async_client: {e}")
                        pass
                api_key = api_key.strip().strip('"').strip("'")
            self._async_client = AsyncOpenAI(api_key=api_key, timeout=self.settings.openai_timeout)
        return self._async_client

    @property
    def sync_client(self) -> OpenAI:
        """Get sync OpenAI client."""
        if self._sync_client is None:
            # Ensure api_key is a clean string, not JSON
            api_key = self.api_key
            if isinstance(api_key, str):
                api_key = api_key.strip().strip('"').strip("'")
                # If it looks like JSON, try to extract the actual key
                if api_key.startswith('{') and api_key.endswith('}'):
                    try:
                        import json
                        parsed = json.loads(api_key)
                        if isinstance(parsed, dict):
                            for key in ["OPENAI_API_KEY", "openai_api_key", "api_key", "value"]:
                                if key in parsed and isinstance(parsed[key], str):
                                    api_key = parsed[key]
                                    break
                    except Exception:
                        pass
                api_key = api_key.strip().strip('"').strip("'")
            self._sync_client = OpenAI(api_key=api_key, timeout=self.settings.openai_timeout)
        return self._sync_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def create_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """Create chat completion with retry."""
        model_name = model or self.settings.openai_model
        max_tokens_value = max_tokens or self.settings.openai_max_tokens
        
        # Use correct parameter based on model
        if requires_max_completion_tokens(model_name):
            kwargs["max_completion_tokens"] = max_tokens_value
        else:
            kwargs["max_tokens"] = max_tokens_value
        
        return await self.async_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature or self.settings.openai_temperature,
            **kwargs,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def create_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
    ):
        """Create embedding with retry."""
        kwargs = {}
        if dimensions:
            kwargs["dimensions"] = dimensions

        return await self.async_client.embeddings.create(
            model=model or self.settings.openai_embedding_model,
            input=text,
            **kwargs,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def moderate(self, input_text: str):
        """Moderate content with retry."""
        return await self.async_client.moderations.create(input=input_text)


class LLMFactory:
    """Factory for creating OpenAI clients."""

    def __init__(self, settings: Settings, secrets_manager: SecretsManager):
        """Initialize LLM factory."""
        self.settings = settings
        self.secrets_manager = secrets_manager
        self._clients: dict[str, OpenAIClientWrapper] = {}
    
    def _clean_api_key(self, api_key: str) -> str:
        """Clean API key from any JSON artifacts."""
        api_key = api_key.strip().strip('"').strip("'")
        if api_key.startswith('{') and api_key.endswith('}'):
            try:
                import json
                parsed = json.loads(api_key)
                if isinstance(parsed, dict):
                    for key in ["OPENAI_API_KEY", "openai_api_key", "api_key", "value"]:
                        if key in parsed:
                            api_key = parsed[key]
                            break
            except Exception as e:
                logger.error(f"Error extracting from JSON: {e}")
                pass
        api_key = api_key.strip().strip('"').strip("'")
        return api_key

    async def get_client(self, agent_id: Optional[str] = None) -> OpenAIClientWrapper:
        """Get OpenAI client for agent (cached per agent)."""
        cache_key = agent_id or "default"

        if cache_key not in self._clients:
            # Get API key from settings or Secrets Manager
            api_key = self.settings.openai_api_key
            if not api_key:
                try:
                    api_key = await self.secrets_manager.get_openai_api_key()
                except Exception as e:
                    logger.error(f"Failed to get API key from Secrets Manager: {e}")
                    raise RuntimeError(
                        "OpenAI API key not found in settings or Secrets Manager"
                    ) from e

            # Clean API key before creating client
            api_key = self._clean_api_key(api_key)
            self._clients[cache_key] = OpenAIClientWrapper(api_key, self.settings)

        return self._clients[cache_key]

    def clear_cache(self, agent_id: Optional[str] = None) -> None:
        """Clear cached client."""
        if agent_id:
            self._clients.pop(agent_id, None)
        else:
            self._clients.clear()


@lru_cache()
def get_llm_factory() -> LLMFactory:
    """Get cached LLM factory instance."""
    settings = get_settings()
    secrets_manager = get_secrets_manager()
    return LLMFactory(settings, secrets_manager)






