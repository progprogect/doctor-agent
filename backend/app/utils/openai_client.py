"""OpenAI client wrapper with retry logic."""

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


class OpenAIClientWrapper:
    """OpenAI client wrapper with retry and error handling."""

    def __init__(self, api_key: str, settings: Settings):
        """Initialize OpenAI client."""
        self.api_key = api_key
        self.settings = settings
        self._async_client: Optional[AsyncOpenAI] = None
        self._sync_client: Optional[OpenAI] = None

    @property
    def async_client(self) -> AsyncOpenAI:
        """Get async OpenAI client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(api_key=self.api_key, timeout=self.settings.openai_timeout)
        return self._async_client

    @property
    def sync_client(self) -> OpenAI:
        """Get sync OpenAI client."""
        if self._sync_client is None:
            self._sync_client = OpenAI(api_key=self.api_key, timeout=self.settings.openai_timeout)
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
                    raise RuntimeError(
                        "OpenAI API key not found in settings or Secrets Manager"
                    ) from e

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

