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

logger = logging.getLogger(__name__)


class OpenAIClientWrapper:
    """OpenAI client wrapper with retry and error handling."""

    def __init__(self, api_key: str, settings: Settings):
        """Initialize OpenAI client."""
        logger.info(f"[OPENAI_CLIENT] __init__() called with api_key (first 20 chars): {repr(api_key[:20]) if len(api_key) > 20 else repr(api_key)}")
        # Ensure API key is clean (no JSON artifacts)
        api_key = api_key.strip().strip('"').strip("'")
        if api_key.startswith('{') and api_key.endswith('}'):
            logger.warning(f"[OPENAI_CLIENT] API key looks like JSON in __init__! Attempting extraction...")
            try:
                import json
                parsed = json.loads(api_key)
                if isinstance(parsed, dict):
                    for key in ["OPENAI_API_KEY", "openai_api_key", "api_key", "value"]:
                        if key in parsed:
                            api_key = parsed[key]
                            logger.info(f"[OPENAI_CLIENT] Extracted from JSON using key '{key}': {repr(api_key[:20])}...")
                            break
            except Exception as e:
                logger.error(f"[OPENAI_CLIENT] Error extracting from JSON in __init__: {e}")
                pass
        api_key = api_key.strip().strip('"').strip("'")
        logger.info(f"[OPENAI_CLIENT] Final api_key stored in self.api_key (first 10 chars): {repr(api_key[:10])}..., starts_with_sk: {api_key.startswith('sk-')}, starts_with_brace: {api_key.startswith('{')}")
        self.api_key = api_key
        self.settings = settings
        self._async_client: Optional[AsyncOpenAI] = None
        self._sync_client: Optional[OpenAI] = None

    @property
    def async_client(self) -> AsyncOpenAI:
        """Get async OpenAI client."""
        if self._async_client is None:
            logger.info(f"[OPENAI_CLIENT] Creating async_client, self.api_key (first 20 chars): {repr(self.api_key[:20]) if len(self.api_key) > 20 else repr(self.api_key)}")
            # Ensure api_key is a clean string, not JSON
            api_key = self.api_key
            if isinstance(api_key, str):
                api_key = api_key.strip().strip('"').strip("'")
                # If it looks like JSON, try to extract the actual key
                if api_key.startswith('{') and api_key.endswith('}'):
                    logger.warning(f"[OPENAI_CLIENT] api_key looks like JSON in async_client property! Attempting extraction...")
                    try:
                        import json
                        parsed = json.loads(api_key)
                        if isinstance(parsed, dict):
                            for key in ["OPENAI_API_KEY", "openai_api_key", "api_key", "value"]:
                                if key in parsed and isinstance(parsed[key], str):
                                    api_key = parsed[key]
                                    logger.info(f"[OPENAI_CLIENT] Extracted from JSON: {repr(api_key[:20])}...")
                                    break
                    except Exception as e:
                        logger.error(f"[OPENAI_CLIENT] Error extracting from JSON in async_client: {e}")
                        pass
                api_key = api_key.strip().strip('"').strip("'")
            logger.info(f"[OPENAI_CLIENT] Creating AsyncOpenAI with api_key (first 10 chars): {repr(api_key[:10])}..., starts_with_sk: {api_key.startswith('sk-')}")
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
        return await self.async_client.chat.completions.create(
            model=model or self.settings.openai_model,
            messages=messages,
            temperature=temperature or self.settings.openai_temperature,
            max_tokens=max_tokens or self.settings.openai_max_tokens,
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
        logger.info(f"[LLM_FACTORY] _clean_api_key() input (first 20 chars): {repr(api_key[:20]) if len(api_key) > 20 else repr(api_key)}")
        api_key = api_key.strip().strip('"').strip("'")
        if api_key.startswith('{') and api_key.endswith('}'):
            logger.warning(f"[LLM_FACTORY] API key looks like JSON! Attempting extraction...")
            try:
                import json
                parsed = json.loads(api_key)
                if isinstance(parsed, dict):
                    for key in ["OPENAI_API_KEY", "openai_api_key", "api_key", "value"]:
                        if key in parsed:
                            api_key = parsed[key]
                            logger.info(f"[LLM_FACTORY] Extracted from JSON using key '{key}': {repr(api_key[:20])}...")
                            break
            except Exception as e:
                logger.error(f"[LLM_FACTORY] Error extracting from JSON: {e}")
                pass
        api_key = api_key.strip().strip('"').strip("'")
        logger.info(f"[LLM_FACTORY] _clean_api_key() output (first 20 chars): {repr(api_key[:20]) if len(api_key) > 20 else repr(api_key)}, starts_with_sk: {api_key.startswith('sk-')}")
        return api_key

    async def get_client(self, agent_id: Optional[str] = None) -> OpenAIClientWrapper:
        """Get OpenAI client for agent (cached per agent)."""
        cache_key = agent_id or "default"

        if cache_key not in self._clients:
            logger.info(f"[LLM_FACTORY] Creating new client for cache_key: {cache_key}")
            # Get API key from settings or Secrets Manager
            api_key = self.settings.openai_api_key
            if not api_key:
                logger.info(f"[LLM_FACTORY] No API key in settings, fetching from Secrets Manager...")
                try:
                    api_key = await self.secrets_manager.get_openai_api_key()
                    logger.info(f"[LLM_FACTORY] Received API key from Secrets Manager (first 10 chars): {repr(api_key[:10])}...")
                except Exception as e:
                    logger.error(f"[LLM_FACTORY] Failed to get API key from Secrets Manager: {e}")
                    raise RuntimeError(
                        "OpenAI API key not found in settings or Secrets Manager"
                    ) from e

            # Clean API key before creating client
            api_key = self._clean_api_key(api_key)
            logger.info(f"[LLM_FACTORY] Creating OpenAIClientWrapper with cleaned API key (first 10 chars): {repr(api_key[:10])}..., starts_with_sk: {api_key.startswith('sk-')}")
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






