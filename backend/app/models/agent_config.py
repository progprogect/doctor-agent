"""Agent configuration model."""

import logging
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class PrivacyConfig(BaseModel):
    """Privacy and data retention configuration."""

    consent_model: str = Field(default="implied_by_chat_start")
    purpose_limitation: str = Field(default="booking_and_communication_only")
    message_retention: dict[str, Any] = Field(default_factory=dict)
    metadata_retention: dict[str, Any] = Field(default_factory=dict)
    training_usage: dict[str, Any] = Field(default_factory=dict)


class SecurityConfig(BaseModel):
    """Security configuration."""

    access_control: str = Field(default="rbac")
    audit_log: bool = Field(default=True)


class ChannelsConfig(BaseModel):
    """Channel configuration."""

    primary: str = Field(default="web_chat")
    supported: list[str] = Field(default_factory=lambda: ["web_chat"])
    future: list[str] = Field(default_factory=list)


class ProfileConfig(BaseModel):
    """Doctor profile configuration."""

    doctor_display_name: str
    clinic_display_name: str
    specialty: str
    languages: list[str] = Field(default_factory=lambda: ["ru", "en"])


class StyleConfig(BaseModel):
    """Communication style configuration."""

    tone: str = Field(default="friendly_professional")
    formality: str = Field(default="semi_formal")
    empathy_level: int = Field(default=7, ge=0, le=10)
    depth_level: int = Field(default=5, ge=0, le=10)
    message_length: str = Field(default="short_to_medium")
    persuasion: str = Field(default="soft")

    @field_validator("empathy_level", "depth_level")
    @classmethod
    def validate_level(cls, v: int) -> int:
        """Validate level values."""
        if not 0 <= v <= 10:
            raise ValueError("Level must be between 0 and 10")
        return v


class WorkingHoursConfig(BaseModel):
    """Working hours configuration."""

    timezone: str = Field(default="Asia/Dubai")
    schedule: dict[str, list[str]] = Field(default_factory=dict)
    after_hours_behavior: dict[str, Any] = Field(default_factory=dict)


class RestrictionsConfig(BaseModel):
    """Medical and legal restrictions."""

    no_diagnosis: bool = Field(default=True)
    no_treatment_recommendations: bool = Field(default=True)
    no_drug_advice: bool = Field(default=True)
    no_test_interpretation: bool = Field(default=True)
    no_pre_procedure_recommendations: bool = Field(default=True)
    no_slot_selection: bool = Field(default=True)
    no_repeat_patients: bool = Field(default=True)
    forbidden_claims: list[str] = Field(default_factory=list)
    content_safety: dict[str, Any] = Field(default_factory=dict)


class HandoffConfig(BaseModel):
    """Handoff configuration."""

    always_possible: bool = Field(default=True)
    immediate_takeover_supported: bool = Field(default=True)
    default_handoff_target: str = Field(default="clinic_admin")
    stop_ai_after_handoff: bool = Field(default=True)


class EscalationConfig(BaseModel):
    """Escalation rules configuration."""

    medical_question_policy: str = Field(default="handoff_or_book")
    urgent_case_policy: str = Field(default="advise_emergency_and_handoff")
    repeat_patient_policy: str = Field(default="handoff_only")
    pre_procedure_policy: str = Field(default="handoff_only")
    triggers: dict[str, Any] = Field(default_factory=dict)
    actions: dict[str, Any] = Field(default_factory=dict)


class LLMConfig(BaseModel):
    """LLM configuration."""

    provider: str = Field(default="openai")
    api: str = Field(default="responses")
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=600, ge=1, le=4096)
    timeout: int = Field(default=30)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        valid_providers = ["openai", "aws_bedrock"]
        if v not in valid_providers:
            raise ValueError(f"LLM provider must be one of: {', '.join(valid_providers)}")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature value."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("max_output_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max_output_tokens value."""
        if v < 1:
            raise ValueError("max_output_tokens must be at least 1")
        if v > 4096:
            raise ValueError("max_output_tokens cannot exceed 4096")
        return v


class EmbeddingsConfig(BaseModel):
    """Embeddings configuration."""

    provider: str = Field(default="openai")
    model: str = Field(default="text-embedding-3-small")
    dimensions: int = Field(default=1536)
    batch_size: int = Field(default=100)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate embeddings provider."""
        valid_providers = ["openai", "aws_bedrock"]
        if v not in valid_providers:
            raise ValueError(
                f"Embeddings provider must be one of: {', '.join(valid_providers)}"
            )
        return v

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        """Validate embedding dimensions."""
        if v < 1:
            raise ValueError("Dimensions must be at least 1")
        if v > 8192:
            raise ValueError("Dimensions cannot exceed 8192")
        return v


class ModerationConfig(BaseModel):
    """Moderation configuration."""

    provider: str = Field(default="openai")
    enabled: bool = Field(default=True)
    mode: str = Field(default="pre_and_post")
    categories: list[str] = Field(default_factory=list)
    action_on_violation: str = Field(default="block_and_escalate")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate moderation provider."""
        valid_providers = ["openai"]
        if v not in valid_providers:
            raise ValueError(
                f"Moderation provider must be one of: {', '.join(valid_providers)}"
            )
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate moderation mode."""
        valid_modes = ["pre", "post", "pre_and_post"]
        if v not in valid_modes:
            raise ValueError(f"Moderation mode must be one of: {', '.join(valid_modes)}")
        return v


class ConversationExample(BaseModel):
    """Example conversation for few-shot learning."""

    id: str
    user_message: str = Field(..., min_length=1, max_length=500)
    agent_response: str = Field(..., min_length=1, max_length=2000)
    category: Optional[str] = Field(
        None, description="Example category: booking, info, hours, custom"
    )


class PromptsConfig(BaseModel):
    """Prompts configuration."""

    system: dict[str, str] = Field(default_factory=dict)
    templates: dict[str, str] = Field(default_factory=dict)
    examples: list[ConversationExample] = Field(
        default_factory=list,
        description="Few-shot examples for style guidance (English)",
    )


class RAGConfig(BaseModel):
    """RAG configuration."""

    enabled: bool = Field(default=True)
    vector_store: dict[str, Any] = Field(default_factory=dict)
    retrieval: dict[str, Any] = Field(default_factory=dict)
    scope: str = Field(default="agent_only")
    sources: list[dict[str, Any]] = Field(default_factory=list)


class MonitoringConfig(BaseModel):
    """Monitoring and quality configuration."""

    admin_panel_required: bool = Field(default=True)
    flags: dict[str, Any] = Field(default_factory=dict)
    kpi_targets_mvp: dict[str, float] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Complete agent configuration."""

    version: str = Field(default="1.0")
    agent_id: str
    role: str = Field(default="instagram_doctor_agent")
    project: str
    environment: str = Field(default="mvp")

    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    profile: ProfileConfig
    style: StyleConfig = Field(default_factory=StyleConfig)
    working_hours: WorkingHoursConfig = Field(default_factory=WorkingHoursConfig)
    restrictions: RestrictionsConfig = Field(default_factory=RestrictionsConfig)
    handoff: HandoffConfig = Field(default_factory=HandoffConfig)
    escalation: EscalationConfig = Field(default_factory=EscalationConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    moderation: ModerationConfig = Field(default_factory=ModerationConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    @model_validator(mode="after")
    def validate_config(self) -> "AgentConfig":
        """Cross-field validation."""
        # Ensure profile is set (required field)
        if not self.profile.doctor_display_name:
            raise ValueError("doctor_display_name is required in profile")
        if not self.profile.clinic_display_name:
            raise ValueError("clinic_display_name is required in profile")

        # Validate RAG configuration if enabled
        if self.rag.enabled:
            if "top_k" in self.rag.retrieval:
                top_k = self.rag.retrieval["top_k"]
                if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
                    raise ValueError("RAG top_k must be an integer between 1 and 50")

            if "score_threshold" in self.rag.retrieval:
                threshold = self.rag.retrieval["score_threshold"]
                if not isinstance(threshold, (int, float)) or not 0.0 <= threshold <= 1.0:
                    raise ValueError("RAG score_threshold must be between 0.0 and 1.0")

        # Validate examples configuration
        if self.prompts.examples:
            if len(self.prompts.examples) > 7:
                raise ValueError("Maximum 7 examples allowed (3 standard + 4 custom)")

        return self

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
        """Create AgentConfig from dictionary (e.g., from YAML)."""
        # Handle nested structures
        config_data = {}
        for key, value in data.items():
            if key == "privacy" and isinstance(value, dict):
                config_data[key] = PrivacyConfig(**value)
            elif key == "security" and isinstance(value, dict):
                config_data[key] = SecurityConfig(**value)
            elif key == "channels" and isinstance(value, dict):
                config_data[key] = ChannelsConfig(**value)
            elif key == "profile" and isinstance(value, dict):
                config_data[key] = ProfileConfig(**value)
            elif key == "style" and isinstance(value, dict):
                config_data[key] = StyleConfig(**value)
            elif key == "working_hours" and isinstance(value, dict):
                config_data[key] = WorkingHoursConfig(**value)
            elif key == "restrictions" and isinstance(value, dict):
                config_data[key] = RestrictionsConfig(**value)
            elif key == "handoff" and isinstance(value, dict):
                config_data[key] = HandoffConfig(**value)
            elif key == "escalation" and isinstance(value, dict):
                config_data[key] = EscalationConfig(**value)
            elif key == "llm" and isinstance(value, dict):
                config_data[key] = LLMConfig(**value)
            elif key == "embeddings" and isinstance(value, dict):
                config_data[key] = EmbeddingsConfig(**value)
            elif key == "moderation" and isinstance(value, dict):
                config_data[key] = ModerationConfig(**value)
            elif key == "prompts" and isinstance(value, dict):
                # Handle examples conversion if present
                prompts_data = value.copy()
                if "examples" in prompts_data and isinstance(prompts_data["examples"], list):
                    prompts_data["examples"] = [
                        ConversationExample(**ex) if isinstance(ex, dict) else ex
                        for ex in prompts_data["examples"]
                    ]
                config_data[key] = PromptsConfig(**prompts_data)
            elif key == "rag" and isinstance(value, dict):
                config_data[key] = RAGConfig(**value)
            elif key == "monitoring" and isinstance(value, dict):
                config_data[key] = MonitoringConfig(**value)
            else:
                config_data[key] = value

        return cls(**config_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert AgentConfig to dictionary."""
        return self.model_dump(exclude_none=True)

