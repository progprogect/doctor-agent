/** Step 5: LLM Settings. */

"use client";

import React from "react";
import { Select } from "@/components/shared/Select";
import { Slider } from "@/components/shared/Slider";
import { Input } from "@/components/shared/Input";
import type { AgentConfigFormData } from "@/lib/utils/agentConfig";
import type { ValidationError } from "@/lib/utils/validation";
import { getFieldError } from "@/lib/utils/validation";

interface LLMStepProps {
  config: Partial<AgentConfigFormData>;
  errors: ValidationError[];
  onUpdate: (config: Partial<AgentConfigFormData>) => void;
}

const MODEL_OPTIONS = [
  // GPT-5 Series (Latest & Best)
  { value: "gpt-5.2", label: "GPT-5.2 (Latest, Best for Agents) ⭐", description: "Best model for coding and agentic tasks across industries" },
  { value: "gpt-5.1", label: "GPT-5.1 (Best with Reasoning)", description: "Best for coding and agentic tasks with configurable reasoning effort" },
  { value: "gpt-5", label: "GPT-5 (Intelligent Reasoning)", description: "Previous intelligent reasoning model for coding and agentic tasks" },
  { value: "gpt-5-mini", label: "GPT-5 Mini (Fast & Efficient)", description: "Faster, cost-efficient version for well-defined tasks" },
  { value: "gpt-5-nano", label: "GPT-5 Nano (Fastest & Cheapest)", description: "Fastest, most cost-efficient version" },
  
  // GPT-4 Series (Current Standard)
  { value: "gpt-4.1", label: "GPT-4.1 (Smartest Non-Reasoning) ⭐", description: "Smartest non-reasoning model" },
  { value: "gpt-4o", label: "GPT-4o (Fast & Intelligent) ⭐", description: "Fast, intelligent, flexible GPT model" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini (Fast & Affordable) ⭐", description: "Fast, affordable small model for focused tasks" },
  { value: "gpt-4-turbo", label: "GPT-4 Turbo (Legacy)", description: "An older high-intelligence GPT model" },
  { value: "gpt-4", label: "GPT-4 (Legacy)", description: "An older high-intelligence GPT model" },
  
  // GPT-4o Specialized (Preview)
  { value: "gpt-4o-audio-preview", label: "GPT-4o Audio (Preview)", description: "GPT-4o model capable of audio input and output" },
  { value: "gpt-4o-mini-audio-preview", label: "GPT-4o Mini Audio (Preview)", description: "Smaller model capable of audio input and output" },
  { value: "gpt-4o-realtime-preview", label: "GPT-4o Realtime (Preview)", description: "Model capable of realtime text and audio input and output" },
  { value: "gpt-4o-mini-realtime-preview", label: "GPT-4o Mini Realtime (Preview)", description: "Smaller realtime model for text and audio" },
  { value: "gpt-4o-search-preview", label: "GPT-4o Search (Preview)", description: "GPT model for web search in Chat Completion" },
  { value: "gpt-4o-mini-search-preview", label: "GPT-4o Mini Search (Preview)", description: "Fast, affordable small model for web search" },
  
  // Legacy Models
  { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo (Legacy)", description: "Legacy GPT model for cheaper chat and non-chat tasks" },
];

export const LLMStep: React.FC<LLMStepProps> = ({
  config,
  errors,
  onUpdate,
}) => {
  const selectedModel = MODEL_OPTIONS.find(
    (model) => model.value === (config.llm_model || "gpt-4o-mini")
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          LLM Settings
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Configure the language model parameters for agent responses.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="md:col-span-2">
          <Select
            label="Model"
            value={config.llm_model || "gpt-4o-mini"}
            onChange={(e) => onUpdate({ llm_model: e.target.value })}
            options={MODEL_OPTIONS.map(({ value, label }) => ({ value, label }))}
            error={getFieldError(errors, "llm_model")}
          />
          {selectedModel?.description && (
            <p className="mt-1 text-xs text-gray-600 italic">
              {selectedModel.description}
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Choose the OpenAI model for generating responses. Models marked with ⭐ are recommended for medical agents.
          </p>
        </div>

        <div className="md:col-span-2">
          <Slider
            label="Temperature"
            value={config.llm_temperature ?? 0.2}
            min={0}
            max={2}
            step={0.1}
            onChange={(e) =>
              onUpdate({ llm_temperature: parseFloat(e.target.value) })
            }
            error={getFieldError(errors, "llm_temperature")}
          />
          <p className="mt-1 text-xs text-gray-500">
            Controls randomness (0 = deterministic, 2 = very creative). Recommended: 0.2 for consistent responses.
          </p>
        </div>

        <div className="md:col-span-2">
          <Input
            type="number"
            label="Max Output Tokens"
            value={config.llm_max_tokens ?? 600}
            onChange={(e) =>
              onUpdate({ llm_max_tokens: parseInt(e.target.value) || 600 })
            }
            error={getFieldError(errors, "llm_max_tokens")}
            min={1}
            max={4096}
            helperText="Maximum length of generated responses (1-4096 tokens)"
          />
        </div>
      </div>

      {/* Preview */}
      <div className="mt-8 p-6 bg-[#F5D76E]/10 border border-[#D4AF37]/20 rounded-sm">
        <h4 className="text-sm font-medium text-gray-700 mb-4">
          LLM Configuration Preview
        </h4>
        <div className="bg-white p-4 rounded-sm border border-[#D4AF37]/20 space-y-2 text-sm">
          <p className="text-gray-600">
            <strong>Model:</strong> {config.llm_model || "gpt-4o-mini"}
          </p>
          <p className="text-gray-600">
            <strong>Temperature:</strong> {config.llm_temperature ?? 0.2}
          </p>
          <p className="text-gray-600">
            <strong>Max Tokens:</strong> {config.llm_max_tokens ?? 600}
          </p>
        </div>
      </div>
    </div>
  );
};
