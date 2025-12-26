/** Utilities for working with agent configuration. */

export interface AgentConfigFormData {
  // Basic Info
  agent_id: string;
  doctor_display_name: string;
  clinic_display_name: string;
  specialty: string;
  languages?: string[]; // Languages the agent can communicate in

  // Style (Step 2)
  tone?: string;
  formality?: string;
  empathy_level?: number;
  depth_level?: number;
  message_length?: string;
  persuasion?: string;

  // RAG
  rag_enabled: boolean;
  rag_documents: Array<{
    id: string;
    title: string;
    content: string;
  }>;

  // Escalation (Step 4) - Only policies, no keywords
  medical_question_policy?: string;
  urgent_case_policy?: string;
  repeat_patient_policy?: string;
  pre_procedure_policy?: string;

  // LLM Settings (Step 5)
  llm_model?: string;
  llm_temperature?: number;
  llm_max_tokens?: number;

  // System Prompt (Step 6)
  system_persona?: string; // Editable system persona prompt
}

/**
 * Generate default agent configuration.
 */
export function generateDefaultConfig(): Partial<AgentConfigFormData> {
  return {
    rag_enabled: false,
    rag_documents: [],
    languages: ["ru", "en"], // Default languages
    // Style defaults
    tone: "friendly_professional",
    formality: "semi_formal",
    empathy_level: 7,
    depth_level: 5,
    message_length: "short_to_medium",
    persuasion: "soft",
    // Escalation defaults
    medical_question_policy: "handoff_or_book",
    urgent_case_policy: "advise_emergency_and_handoff",
    repeat_patient_policy: "handoff_only",
    pre_procedure_policy: "handoff_only",
    // LLM defaults
    llm_model: "gpt-4o-mini",
    llm_temperature: 0.2,
    llm_max_tokens: 600,
    // System prompt default
    system_persona: "",
  };
}

/**
 * Convert existing agent config to form data (for cloning).
 */
export function agentConfigToFormData(
  agentConfig: Record<string, any>
): Partial<AgentConfigFormData> {
  const formData: Partial<AgentConfigFormData> = {
    // Basic Info
    agent_id: agentConfig.agent_id || "",
    doctor_display_name: agentConfig.profile?.doctor_display_name || "",
    clinic_display_name: agentConfig.profile?.clinic_display_name || "",
    specialty: agentConfig.profile?.specialty || "",

    // Style
    tone: agentConfig.style?.tone,
    formality: agentConfig.style?.formality,
    empathy_level: agentConfig.style?.empathy_level,
    depth_level: agentConfig.style?.depth_level,
    message_length: agentConfig.style?.message_length,
    persuasion: agentConfig.style?.persuasion,

    // RAG
    rag_enabled: agentConfig.rag?.enabled || false,
    rag_documents:
      agentConfig.rag?.sources?.map((source: any, index: number) => ({
        id: source.id || `doc_${index}`,
        title: source.title || "",
        content: source.content || "",
      })) || [],

    // Escalation - only policies
    medical_question_policy: agentConfig.escalation?.medical_question_policy,
    urgent_case_policy: agentConfig.escalation?.urgent_case_policy,
    repeat_patient_policy: agentConfig.escalation?.repeat_patient_policy,
    pre_procedure_policy: agentConfig.escalation?.pre_procedure_policy,

    // Languages
    languages: agentConfig.profile?.languages || ["ru", "en"],

    // System prompt
    system_persona: agentConfig.prompts?.system?.persona,

    // LLM
    llm_model: agentConfig.llm?.model,
    llm_temperature: agentConfig.llm?.temperature,
    llm_max_tokens: agentConfig.llm?.max_output_tokens,
  };

  return formData;
}

/**
 * Convert form data to agent config object (for API).
 */
export function formDataToAgentConfig(
  formData: AgentConfigFormData
): Record<string, any> {
  // Minimal configuration - only fields that are actually used in the code
  const config: Record<string, any> = {
    agent_id: formData.agent_id,
    project: formData.clinic_display_name || "Default Project", // Required by backend model
    profile: {
      doctor_display_name: formData.doctor_display_name,
      clinic_display_name: formData.clinic_display_name,
      specialty: formData.specialty,
      languages: formData.languages || ["ru", "en"],
    },
    style: {
      tone: formData.tone || "friendly_professional",
      formality: formData.formality || "semi_formal",
      empathy_level: formData.empathy_level ?? 7,
      depth_level: formData.depth_level ?? 5,
      message_length: formData.message_length || "short_to_medium",
      persuasion: formData.persuasion || "soft",
    },
    llm: {
      provider: "openai",
      api: "responses",
      model: formData.llm_model || "gpt-4o-mini",
      temperature: formData.llm_temperature ?? 0.2,
      max_output_tokens: formData.llm_max_tokens ?? 600,
      timeout: 30,
    },
    prompts: {
      system: {
        persona: formData.system_persona || `Ты общаешься от лица врача ${formData.doctor_display_name} из ${formData.clinic_display_name}.
Твой стиль — дружелюбный и профессиональный. Ты помогаешь с информацией и записью.
Ты НЕ ведёшь медицинскую консультацию в чате.`,
        hard_rules: `Запрещено: диагнозы, лечение, рекомендации препаратов, интерпретация анализов.
Любые медицинские вопросы переводишь в запись на очный приём или передаёшь человеку.
В срочных случаях рекомендуешь экстренную помощь и прекращаешь самостоятельное общение.
Повторные пациенты — только человек.
После получения телефона/контакта: передай администратору и прекрати диалог.
Не обещай результатов. Не утверждай, что врач лично читает прямо сейчас.`,
        goal: `Главная цель — быстро и вежливо помочь, квалифицировать запрос и привести к записи без давления.
Если специализация не подходит — предложи другого врача/направление и запись.`,
      },
    },
    rag: {
      enabled: formData.rag_enabled,
      vector_store: {
        provider: "opensearch",
        index_name: `agent_${formData.agent_id}_documents`,
      },
      retrieval: {
        top_k: 6,
        score_threshold: 0.2,
      },
      scope: "agent_only",
      sources: formData.rag_enabled
        ? formData.rag_documents.map((doc) => ({
            id: doc.id,
            type: "text",
            title: doc.title,
            content: doc.content,
          }))
        : [],
    },
    moderation: {
      provider: "openai",
      enabled: true,
      mode: "pre_and_post",
    },
    escalation: {
      medical_question_policy: formData.medical_question_policy || "handoff_or_book",
      urgent_case_policy: formData.urgent_case_policy || "advise_emergency_and_handoff",
      repeat_patient_policy: formData.repeat_patient_policy || "handoff_only",
      pre_procedure_policy: formData.pre_procedure_policy || "handoff_only",
    },
  };

  return config;
}

/**
 * Transliterate Russian/Cyrillic characters to Latin.
 * Handles both uppercase and lowercase Cyrillic characters.
 */
function transliterate(text: string): string {
  // Map for lowercase Cyrillic characters
  const lowercaseMap: Record<string, string> = {
    а: "a", б: "b", в: "v", г: "g", д: "d", е: "e", ё: "yo", ж: "zh",
    з: "z", и: "i", й: "y", к: "k", л: "l", м: "m", н: "n", о: "o",
    п: "p", р: "r", с: "s", т: "t", у: "u", ф: "f", х: "kh", ц: "ts",
    ч: "ch", ш: "sh", щ: "shch", ъ: "", ы: "y", ь: "", э: "e", ю: "yu",
    я: "ya",
  };

  // Map for uppercase Cyrillic characters (same transliteration, but we'll lowercase later)
  const uppercaseMap: Record<string, string> = {
    А: "a", Б: "b", В: "v", Г: "g", Д: "d", Е: "e", Ё: "yo", Ж: "zh",
    З: "z", И: "i", Й: "y", К: "k", Л: "l", М: "m", Н: "n", О: "o",
    П: "p", Р: "r", С: "s", Т: "t", У: "u", Ф: "f", Х: "kh", Ц: "ts",
    Ч: "ch", Ш: "sh", Щ: "shch", Ъ: "", Ы: "y", Ь: "", Э: "e", Ю: "yu",
    Я: "ya",
  };

  // Combine both maps
  const transliterationMap = { ...lowercaseMap, ...uppercaseMap };

  return text
    .split("")
    .map((char) => transliterationMap[char] || char)
    .join("");
}

/**
 * Generate agent ID from clinic name and doctor name.
 * Transliterates Cyrillic characters to Latin and creates a safe ID.
 */
export function generateAgentId(clinicName: string, doctorName?: string): string {
  let combined = clinicName.trim();
  
  if (doctorName && doctorName.trim()) {
    // Combine clinic and doctor names
    combined = `${clinicName.trim()}_${doctorName.trim()}`;
  }
  
  // Transliterate Cyrillic to Latin
  const transliterated = transliterate(combined);
  
  // Convert to lowercase and replace non-alphanumeric with underscores
  return transliterated
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .substring(0, 50);
}
