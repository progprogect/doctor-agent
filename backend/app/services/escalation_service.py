"""Escalation service using LLM-based detection."""

import logging
from functools import lru_cache
from typing import Optional

from app.chains.escalation_chain import EscalationChain
from app.models.escalation import EscalationDecision, EscalationType
from app.services.llm_factory import LLMFactory, get_llm_factory

logger = logging.getLogger(__name__)


class EscalationService:
    """Service for detecting escalation needs."""

    def __init__(self, llm_factory: LLMFactory):
        """Initialize escalation service."""
        self.llm_factory = llm_factory
        self.escalation_chain = EscalationChain(llm_factory)

    async def detect_escalation(
        self,
        message: str,
        conversation_context: Optional[dict] = None,
        agent_id: Optional[str] = None,
    ) -> EscalationDecision:
        """Detect if message requires escalation."""
        try:
            decision = await self.escalation_chain.detect(
                message=message,
                context=conversation_context,
                agent_id=agent_id,
            )

            if decision.needs_escalation:
                logger.info(
                    f"Escalation detected: {decision.escalation_type.value}",
                    extra={
                        "agent_id": agent_id,
                        "escalation_type": decision.escalation_type.value,
                        "confidence": decision.confidence,
                    },
                )

            return decision
        except Exception as e:
            logger.error(
                f"Escalation detection error for agent {agent_id}: {str(e)}",
                exc_info=True,
                extra={"agent_id": agent_id, "message_length": len(message)},
            )
            # On error, default to no escalation to avoid blocking conversation
            return EscalationDecision(
                needs_escalation=False,
                escalation_type=EscalationType.NONE,
                confidence=0.0,
                reason=f"Error in escalation detection: {str(e)}",
                suggested_action="continue_with_ai",
            )

    async def should_escalate(
        self,
        message: str,
        conversation_context: Optional[dict] = None,
        agent_id: Optional[str] = None,
    ) -> tuple[bool, EscalationDecision]:
        """Check if escalation is needed and return decision."""
        decision = await self.detect_escalation(
            message=message,
            conversation_context=conversation_context,
            agent_id=agent_id,
        )
        return decision.needs_escalation, decision

    def get_escalation_reason(self, decision: EscalationDecision) -> str:
        """Get human-readable escalation reason."""
        if not decision.needs_escalation:
            return "No escalation needed"

        reason_map = {
            EscalationType.URGENT: "Urgent medical situation detected",
            EscalationType.MEDICAL: "Medical question requiring human expertise",
            EscalationType.BOOKING: "User wants to book an appointment",
            EscalationType.REPEAT_PATIENT: "Returning patient - requires human handling",
            EscalationType.NONE: "No escalation needed",
        }

        return reason_map.get(decision.escalation_type, decision.reason)


@lru_cache()
def get_escalation_service() -> EscalationService:
    """Get cached escalation service instance."""
    llm_factory = get_llm_factory()
    return EscalationService(llm_factory)

