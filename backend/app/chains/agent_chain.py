"""Main LangChain agent chain."""

from typing import Optional

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.models.agent_config import AgentConfig
from app.services.llm_factory import LLMFactory
from app.tools.escalation_tool import EscalationTool
from app.tools.booking_tool import BookingTool
from app.services.escalation_service import EscalationService
from app.services.rag_service import RAGService
from app.utils.model_params import requires_max_completion_tokens


class AgentChain:
    """Main agent chain for conversation."""

    def __init__(
        self,
        agent_config: AgentConfig,
        llm_factory: LLMFactory,
        escalation_service: EscalationService,
        rag_service: RAGService,
    ):
        """Initialize agent chain."""
        self.agent_config = agent_config
        self.llm_factory = llm_factory
        self.escalation_service = escalation_service
        self.rag_service = rag_service
        self._executor: Optional[AgentExecutor] = None

    async def _get_executor(self) -> AgentExecutor:
        """Get or create agent executor."""
        if self._executor is None:
            client = await self.llm_factory.get_client(self.agent_config.agent_id)

            # Create LLM with correct parameter based on model
            llm_kwargs = {
                "model": self.agent_config.llm.model,
                "temperature": self.agent_config.llm.temperature,
                "openai_api_key": client.api_key,
                "timeout": self.agent_config.llm.timeout,
            }
            
            # Use max_completion_tokens for o1/o3 and newer models, max_tokens for others
            if requires_max_completion_tokens(self.agent_config.llm.model):
                # For models requiring max_completion_tokens, pass via model_kwargs
                # ChatOpenAI will pass these kwargs directly to OpenAI API
                llm_kwargs["model_kwargs"] = {"max_completion_tokens": self.agent_config.llm.max_output_tokens}
            else:
                llm_kwargs["max_tokens"] = self.agent_config.llm.max_output_tokens
            
            llm = ChatOpenAI(**llm_kwargs)

            # Create tools
            tools = [
                EscalationTool(
                    escalation_service=self.escalation_service,
                    agent_id=self.agent_config.agent_id,
                ),
                BookingTool(agent_id=self.agent_config.agent_id),
            ]

            # Build system prompt from config
            system_prompt = self._build_system_prompt()

            # Create prompt template
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )

            # Create agent
            agent = create_openai_tools_agent(llm, tools, prompt)

            # Create executor
            self._executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
            )

        return self._executor

    def _build_system_prompt(self) -> str:
        """Build system prompt from agent config."""
        prompts = self.agent_config.prompts.system

        # Format persona with profile information
        persona = prompts.get("persona", "").format(
            doctor_display_name=self.agent_config.profile.doctor_display_name,
            clinic_display_name=self.agent_config.profile.clinic_display_name,
            specialty=self.agent_config.profile.specialty,
        )

        hard_rules = prompts.get("hard_rules", "")
        goal = prompts.get("goal", "")

        # Build profile information section
        profile = self.agent_config.profile
        languages_str = ", ".join(profile.languages)
        profile_info = f"""
Profile Information:
- Doctor: {profile.doctor_display_name}
- Clinic: {profile.clinic_display_name}
- Specialty: {profile.specialty}
- Languages: {languages_str}

You can communicate in these languages. Respond in the same language the user uses, or ask which language they prefer if unclear.
"""

        # Build style description from config
        style = self.agent_config.style
        style_description = f"""
Communication Style Guidelines:
- Tone: {style.tone.replace('_', ' ').title()}
- Formality Level: {style.formality.replace('_', ' ').title()}
- Empathy Level: {style.empathy_level}/10 (higher = more empathetic and understanding)
- Depth Level: {style.depth_level}/10 (higher = more detailed responses)
- Message Length: {style.message_length.replace('_', ' ').title()}
- Persuasion Approach: {style.persuasion.title()} (soft = gentle suggestions, strong = more direct)

Apply these style guidelines consistently in all your responses. Adjust your communication to match these parameters while maintaining professionalism and medical safety.
"""

        # Build few-shot examples section (English only)
        examples_section = ""
        if self.agent_config.prompts.examples:
            examples_list = []
            for i, example in enumerate(self.agent_config.prompts.examples, 1):
                examples_list.append(
                    f"Example {i}:\n"
                    f"User: {example.user_message}\n"
                    f"Agent: {example.agent_response}"
                )

            examples_section = f"""
Examples of desired communication style:

{chr(10).join(examples_list)}

Follow these examples as a guide for your communication style, tone, and approach. 
Match the level of formality, empathy, and detail shown in these examples. 
Note: These examples are in English, but you should respond in the language 
the user uses (as specified in your language capabilities).
"""

        # Build final prompt with proper spacing
        prompt_parts = [
            persona,
            profile_info,
            hard_rules,
            goal,
            style_description,
        ]
        
        if examples_section:
            prompt_parts.append(examples_section)
        
        prompt_parts.append("""Remember:
- Be friendly and professional
- Never provide medical diagnoses or treatment advice
- Escalate urgent or medical questions to human
- Help with booking appointments
- Use available tools when needed
""")
        
        return "\n\n".join(prompt_parts)

    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[list[dict]] = None,
        rag_context: Optional[str] = None,
    ) -> str:
        """Generate response using agent chain."""
        executor = await self._get_executor()

        # Prepare input with context
        input_text = user_message
        if rag_context:
            input_text = f"Context:\n{rag_context}\n\nUser message: {user_message}"

        # Prepare chat history (last 50 messages for context)
        # Note: Consider token limits - 50 messages ≈ 2000-3000 tokens
        chat_history = []
        if conversation_history:
            # conversation_history is already in chronological order (oldest first)
            # Take last 50 messages (most recent)
            for msg in conversation_history[-50:]:  # Last 50 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # Normalize role to lowercase for comparison
                role_lower = role.lower() if isinstance(role, str) else str(role).lower()
                if role_lower == "user":
                    chat_history.append(("human", content))
                elif role_lower == "agent":
                    chat_history.append(("ai", content))

        try:
            result = await executor.ainvoke(
                {
                    "input": input_text,
                    "chat_history": chat_history,
                }
            )
            return result.get("output", "I apologize, but I couldn't generate a response.")
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

