"""Escalation service using LLM-based detection."""

import logging
import re
from typing import Optional

from app.chains.escalation_chain import EscalationChain
from app.models.agent_config import AgentConfig
from app.models.escalation import EscalationDecision, EscalationType
from app.services.llm_factory import LLMFactory, get_llm_factory

logger = logging.getLogger(__name__)


class EscalationService:
    """Service for detecting escalation needs."""

    def __init__(self, llm_factory: LLMFactory, agent_config: Optional[AgentConfig] = None):
        """Initialize escalation service."""
        self.llm_factory = llm_factory
        self.agent_config = agent_config
        self.escalation_chain = EscalationChain(llm_factory, agent_config)

    def _detect_phone_number(
        self, message: str, agent_config: Optional[AgentConfig] = None
    ) -> Optional[str]:
        """Detect phone number in message using regex from config."""
        config = agent_config or self.agent_config
        if not config:
            return None

        phone_config = config.escalation.phone_detection
        if not phone_config.get("enabled", False):
            return None

        regex_pattern = phone_config.get("regex", r"(\+?\d[\d\s\-\(\)]{7,}\d)")
        try:
            matches = re.findall(regex_pattern, message)
            if matches:
                # Return first match
                return matches[0].strip()
        except re.error as e:
            logger.warning(
                f"Invalid phone detection regex: {e}",
                extra={"regex": regex_pattern},
            )

        return None

    async def detect_escalation(
        self,
        message: str,
        conversation_context: Optional[dict] = None,
        agent_id: Optional[str] = None,
        agent_config: Optional[AgentConfig] = None,
    ) -> EscalationDecision:
        """Detect if message requires escalation."""
        # Use provided agent_config or fallback to instance config
        config = agent_config or self.agent_config

        # Check phone number detection first (before LLM)
        if config:
            phone_number = self._detect_phone_number(message, config)
            if phone_number:
                logger.info(
                    f"Phone number detected: {phone_number}",
                    extra={"agent_id": agent_id, "phone": phone_number},
                )
                return EscalationDecision(
                    needs_escalation=True,
                    escalation_type=EscalationType.BOOKING,  # Phone usually means booking intent
                    confidence=1.0,
                    reason=f"Phone number detected: {phone_number}",
                    suggested_action="handoff_for_booking",
                )

        try:
            decision = await self.escalation_chain.detect(
                message=message,
                context=conversation_context,
                agent_id=agent_id,
                agent_config=config,
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
        agent_config: Optional[AgentConfig] = None,
    ) -> tuple[bool, EscalationDecision]:
        """Check if escalation is needed and return decision."""
        decision = await self.detect_escalation(
            message=message,
            conversation_context=conversation_context,
            agent_id=agent_id,
            agent_config=agent_config,
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


def create_escalation_service(
    agent_config: Optional[AgentConfig] = None,
) -> EscalationService:
    """Create escalation service instance with optional agent config."""
    llm_factory = get_llm_factory()
    return EscalationService(llm_factory, agent_config)


# Keep backward compatibility
def get_escalation_service() -> EscalationService:
    """Get escalation service instance without agent config (backward compatibility)."""
    return create_escalation_service(None)

