/** Step 4: Escalation Rules. */

"use client";

import React, { useState } from "react";
import { Input } from "@/components/shared/Input";
import { Button } from "@/components/shared/Button";
import type { AgentConfigFormData } from "@/lib/utils/agentConfig";
import type { ValidationError } from "@/lib/utils/validation";

interface EscalationStepProps {
  config: Partial<AgentConfigFormData>;
  errors: ValidationError[];
  onUpdate: (config: Partial<AgentConfigFormData>) => void;
}

export const EscalationStep: React.FC<EscalationStepProps> = ({
  config,
  onUpdate,
}) => {
  const triggers = config.escalation_triggers || {
    urgent_keywords: [],
    medical_question_keywords: [],
    repeat_patient_keywords: [],
    booking_keywords: [],
  };

  const [editingCategory, setEditingCategory] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState<string>("");

  const categories = [
    {
      key: "urgent_keywords",
      label: "Urgent Keywords",
      description: "Keywords that trigger immediate escalation for urgent cases",
      default: [
        "срочно",
        "немедленно",
        "сильная боль",
        "кровотечение",
        "теряю сознание",
        "не могу дышать",
        "температура 40",
        "ребёнок",
        "беременность",
      ],
    },
    {
      key: "medical_question_keywords",
      label: "Medical Question Keywords",
      description: "Keywords that indicate medical questions requiring human expertise",
      default: [
        "диагноз",
        "что со мной",
        "какое лечение",
        "какие таблетки",
        "можно ли принимать",
        "анализы",
        "расшифруйте",
        "симптом",
        "болит",
      ],
    },
    {
      key: "repeat_patient_keywords",
      label: "Repeat Patient Keywords",
      description: "Keywords that indicate returning patients",
      default: [
        "я уже был(а)",
        "повторно",
        "после прошлой процедуры",
        "у меня уже есть карта",
        "наблюдаюсь",
      ],
    },
    {
      key: "booking_keywords",
      label: "Booking Keywords",
      description: "Keywords that indicate appointment booking intent",
      default: ["записаться", "запись", "приём", "консультация", "appointment"],
    },
  ];

  const handleAddKeyword = (categoryKey: string) => {
    if (!editingValue.trim()) return;

    const currentKeywords =
      (triggers[categoryKey as keyof typeof triggers] as string[]) || [];
    const updated = [...currentKeywords, editingValue.trim()];
    onUpdate({
      escalation_triggers: {
        ...triggers,
        [categoryKey]: updated,
      },
    });
    setEditingValue("");
    setEditingCategory(null);
  };

  const handleRemoveKeyword = (categoryKey: string, index: number) => {
    const currentKeywords =
      (triggers[categoryKey as keyof typeof triggers] as string[]) || [];
    const updated = currentKeywords.filter((_, i) => i !== index);
    onUpdate({
      escalation_triggers: {
        ...triggers,
        [categoryKey]: updated,
      },
    });
  };

  const handleResetToDefaults = (categoryKey: string) => {
    const category = categories.find((c) => c.key === categoryKey);
    if (category) {
      onUpdate({
        escalation_triggers: {
          ...triggers,
          [categoryKey]: category.default,
        },
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Escalation Rules
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Configure keywords and triggers that will escalate conversations to
          human agents.
        </p>
      </div>

      <div className="space-y-6">
        {categories.map((category) => {
          const keywords =
            (triggers[category.key as keyof typeof triggers] as string[]) || [];

          return (
            <div
              key={category.key}
              className="p-4 bg-gray-50 rounded-sm border border-gray-200"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900">
                    {category.label}
                  </h4>
                  <p className="text-xs text-gray-500 mt-1">
                    {category.description}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleResetToDefaults(category.key)}
                >
                  Reset to Defaults
                </Button>
              </div>

              <div className="flex flex-wrap gap-2 mb-3">
                {keywords.map((keyword, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-300 rounded-sm text-sm text-gray-700"
                  >
                    {keyword}
                    <button
                      type="button"
                      onClick={() => handleRemoveKeyword(category.key, index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>

              {editingCategory === category.key ? (
                <div className="flex gap-2">
                  <Input
                    value={editingValue}
                    onChange={(e) => setEditingValue(e.target.value)}
                    placeholder="Enter keyword"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleAddKeyword(category.key);
                      }
                    }}
                    className="flex-1"
                  />
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleAddKeyword(category.key)}
                  >
                    Add
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setEditingCategory(null);
                      setEditingValue("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setEditingCategory(category.key)}
                >
                  Add Keyword
                </Button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
