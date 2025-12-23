"""Moderation service using OpenAI Moderation API."""

import logging
from functools import lru_cache
from typing import Optional

from app.api.exceptions import RAGServiceError
from app.models.moderation import ModerationCategory, ModerationResult
from app.services.llm_factory import LLMFactory, get_llm_factory

logger = logging.getLogger(__name__)


class ModerationService:
    """Service for content moderation."""

    def __init__(self, llm_factory: LLMFactory):
        """Initialize moderation service."""
        self.llm_factory = llm_factory

    async def moderate(
        self, content: str, agent_id: Optional[str] = None
    ) -> ModerationResult:
        """Moderate content using OpenAI Moderation API."""
        client = await self.llm_factory.get_client(agent_id)

        try:
            response = await client.moderate(content)
            result = response.results[0]

            # Map OpenAI categories to our enum
            categories = {}
            category_scores = {}
            primary_category = None
            max_score = 0.0

            for category, flagged in result.categories.model_dump().items():
                score = getattr(result.category_scores, category, 0.0)
                categories[category] = bool(flagged)
                category_scores[category] = float(score)

                if flagged and score > max_score:
                    max_score = score
                    # Map to our enum
                    category_mapping = {
                        "hate": ModerationCategory.HATE,
                        "harassment": ModerationCategory.HARASSMENT,
                        "sexual": ModerationCategory.SEXUAL,
                        "self-harm": ModerationCategory.SELF_HARM,
                        "violence": ModerationCategory.VIOLENCE,
                    }
                    primary_category = category_mapping.get(
                        category, ModerationCategory.NONE
                    )

            return ModerationResult(
                flagged=result.flagged,
                categories=categories,
                category_scores=category_scores,
                category=primary_category or ModerationCategory.NONE,
            )
        except Exception as e:
            # On error, assume not flagged to avoid blocking legitimate content
            # Log error for monitoring
            logger.error(
                f"Moderation API error for agent {agent_id}: {str(e)}",
                exc_info=True,
                extra={"agent_id": agent_id, "content_length": len(content)},
            )
            return ModerationResult(
                flagged=False,
                categories={},
                category_scores={},
                category=ModerationCategory.NONE,
            )

    async def check_pre_moderation(
        self, message: str, agent_id: Optional[str] = None
    ) -> tuple[bool, Optional[ModerationResult]]:
        """Check message before processing (pre-moderation)."""
        result = await self.moderate(message, agent_id)
        return result.flagged, result if result.flagged else None

    async def check_post_moderation(
        self, response: str, agent_id: Optional[str] = None
    ) -> tuple[bool, Optional[ModerationResult]]:
        """Check agent response after generation (post-moderation)."""
        result = await self.moderate(response, agent_id)
        return result.flagged, result if result.flagged else None


@lru_cache()
def get_moderation_service() -> ModerationService:
    """Get cached moderation service instance."""
    llm_factory = get_llm_factory()
    return ModerationService(llm_factory)

