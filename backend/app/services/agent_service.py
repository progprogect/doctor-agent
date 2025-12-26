"""Agent service - LangChain orchestrator."""

import logging
from functools import lru_cache
from typing import Optional

from app.api.exceptions import MessageProcessingError
from app.chains.agent_chain import AgentChain
from app.models.agent_config import AgentConfig
from app.models.conversation import ConversationStatus
from app.services.escalation_service import EscalationService, get_escalation_service
from app.services.llm_factory import LLMFactory, get_llm_factory
from app.services.moderation_service import ModerationService, get_moderation_service
from app.services.rag_service import RAGService, get_rag_service
from app.storage.dynamodb import DynamoDBClient

logger = logging.getLogger(__name__)


class AgentService:
    """Service for agent orchestration."""

    def __init__(
        self,
        agent_config: AgentConfig,
        llm_factory: LLMFactory,
        escalation_service: EscalationService,
        moderation_service: ModerationService,
        rag_service: RAGService,
        dynamodb: DynamoDBClient,
    ):
        """Initialize agent service."""
        self.agent_config = agent_config
        self.llm_factory = llm_factory
        self.escalation_service = escalation_service
        self.moderation_service = moderation_service
        self.rag_service = rag_service
        self.dynamodb = dynamodb
        self.agent_chain = AgentChain(
            agent_config=agent_config,
            llm_factory=llm_factory,
            escalation_service=escalation_service,
            rag_service=rag_service,
        )

    async def process_message(
        self,
        user_message: str,
        conversation_id: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> dict:
        """Process user message and generate response."""
        # Pre-moderation check
        if self.agent_config.moderation.enabled:
            flagged, moderation_result = await self.moderation_service.check_pre_moderation(
                user_message, self.agent_config.agent_id
            )
            if flagged:
                # Update conversation status
                await self.dynamodb.update_conversation(
                    conversation_id=conversation_id,
                    status=ConversationStatus.NEEDS_HUMAN,
                    handoff_reason="Content moderation violation",
                )
                return {
                    "response": None,
                    "escalate": True,
                    "escalation_reason": "Content moderation violation",
                    "moderation_result": moderation_result,
                }

        # Escalation detection
        escalation_decision = await self.escalation_service.detect_escalation(
            message=user_message,
            conversation_context={
                "conversation_id": conversation_id,
                "previous_messages": conversation_history or [],
            },
            agent_id=self.agent_config.agent_id,
        )

        if escalation_decision.needs_escalation:
            # Update conversation status
            await self.dynamodb.update_conversation(
                conversation_id=conversation_id,
                status=ConversationStatus.NEEDS_HUMAN,
                handoff_reason=escalation_decision.reason,
                request_type=escalation_decision.escalation_type.value,
            )

            return {
                "response": None,
                "escalate": True,
                "escalation_reason": escalation_decision.reason,
                "escalation_type": escalation_decision.escalation_type.value,
            }

        # Retrieve RAG context if enabled
        rag_context = None
        if self.agent_config.rag.enabled:
            try:
                rag_context = await self.rag_service.get_formatted_context(
                    query=user_message,
                    agent_id=self.agent_config.agent_id,
                    top_k=self.agent_config.rag.retrieval.get("top_k", 6),
                    score_threshold=self.agent_config.rag.retrieval.get("score_threshold", 0.2),
                )
                if rag_context:
                    logger.debug(
                        f"RAG context retrieved for conversation {conversation_id}",
                        extra={
                            "conversation_id": conversation_id,
                            "agent_id": self.agent_config.agent_id,
                            "context_length": len(rag_context),
                        },
                    )
            except Exception as e:
                # Log error but continue without RAG
                logger.warning(
                    f"RAG retrieval error for conversation {conversation_id}: {str(e)}",
                    exc_info=True,
                    extra={
                        "conversation_id": conversation_id,
                        "agent_id": self.agent_config.agent_id,
                    },
                )

        # Generate response
        try:
            response = await self.agent_chain.generate_response(
                user_message=user_message,
                conversation_history=conversation_history,
                rag_context=rag_context,
            )

            if not response or not response.strip():
                logger.warning(
                    f"Empty response generated for conversation {conversation_id}",
                    extra={
                        "conversation_id": conversation_id,
                        "agent_id": self.agent_config.agent_id,
                    },
                )
                response = "I apologize, but I couldn't generate a response. Please try again."
        except Exception as e:
            logger.error(
                f"Response generation error for conversation {conversation_id}: {str(e)}",
                exc_info=True,
                extra={
                    "conversation_id": conversation_id,
                    "agent_id": self.agent_config.agent_id,
                },
            )
            raise MessageProcessingError(
                f"Failed to generate response: {str(e)}",
                conversation_id=conversation_id,
            )

        # Post-moderation check
        if self.agent_config.moderation.enabled:
            flagged, moderation_result = await self.moderation_service.check_post_moderation(
                response, self.agent_config.agent_id
            )
            if flagged:
                # Update conversation status
                await self.dynamodb.update_conversation(
                    conversation_id=conversation_id,
                    status=ConversationStatus.NEEDS_HUMAN,
                    handoff_reason="Generated content moderation violation",
                )
                return {
                    "response": None,
                    "escalate": True,
                    "escalation_reason": "Generated content moderation violation",
                    "moderation_result": moderation_result,
                }

        return {
            "response": response,
            "escalate": False,
            "rag_context_used": rag_context is not None,
        }


def create_agent_service(
    agent_config: AgentConfig,
    dynamodb: DynamoDBClient,
) -> AgentService:
    """Create agent service instance."""
    llm_factory = get_llm_factory()
    escalation_service = get_escalation_service()
    moderation_service = get_moderation_service()
    rag_service = get_rag_service()

    return AgentService(
        agent_config=agent_config,
        llm_factory=llm_factory,
        escalation_service=escalation_service,
        moderation_service=moderation_service,
        rag_service=rag_service,
        dynamodb=dynamodb,
    )

