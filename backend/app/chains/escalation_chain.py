"""LangChain chain for escalation detection."""

from typing import Optional

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser

from app.config import get_settings
from app.models.escalation import EscalationDecision, EscalationType
from app.services.llm_factory import LLMFactory


class EscalationChain:
    """LangChain chain for detecting escalation needs."""

    def __init__(self, llm_factory: LLMFactory):
        """Initialize escalation chain."""
        self.llm_factory = llm_factory
        self._chain: Optional[LLMChain] = None

    async def _get_chain(self, agent_id: Optional[str] = None) -> LLMChain:
        """Get or create escalation chain."""
        if self._chain is None:
            client = await self.llm_factory.get_client(agent_id)
            settings = get_settings()
            llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.1,  # Low temperature for deterministic classification
                openai_api_key=client.api_key,
                timeout=settings.openai_timeout,
            )

            # Create prompt template
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an escalation detection system for a medical AI agent.
Your task is to analyze user messages and determine if they require human intervention.

Escalation types:
- urgent: Emergency situations, severe symptoms, life-threatening conditions
- medical: Medical questions requiring diagnosis, treatment advice, or interpretation
- booking: User wants to book an appointment
- repeat_patient: User indicates they are a returning/previous patient
- none: No escalation needed, AI can handle

Return a structured response with:
- needs_escalation: boolean
- escalation_type: one of the types above
- confidence: float between 0 and 1
- reason: brief explanation
- suggested_action: what should happen next""",
                    ),
                    ("human", "User message: {message}\n\nConversation context: {context}"),
                ]
            )

            # Create output parser
            output_parser = PydanticOutputParser(pydantic_object=EscalationDecision)

            # Create chain
            self._chain = LLMChain(
                llm=llm,
                prompt=prompt_template,
                output_parser=output_parser,
            )

        return self._chain

    async def detect(
        self,
        message: str,
        context: Optional[dict] = None,
        agent_id: Optional[str] = None,
    ) -> EscalationDecision:
        """Detect if escalation is needed."""
        chain = await self._get_chain(agent_id)

        # Prepare context string
        context_str = ""
        if context:
            context_str = f"Previous messages: {context.get('previous_messages', [])}"
            if context.get("conversation_status"):
                context_str += f"\nStatus: {context['conversation_status']}"

        try:
            result = await chain.ainvoke(
                {
                    "message": message,
                    "context": context_str or "No previous context",
                }
            )
            return result
        except Exception as e:
            # On error, default to no escalation
            return EscalationDecision(
                needs_escalation=False,
                escalation_type=EscalationType.NONE,
                confidence=0.0,
                reason=f"Error in escalation detection: {str(e)}",
                suggested_action="continue_with_ai",
            )

