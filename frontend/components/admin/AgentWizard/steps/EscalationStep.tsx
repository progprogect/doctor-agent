/** Step 4: Escalation Rules. */

"use client";

import React from "react";
import { Select } from "@/components/shared/Select";
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
  const policyOptions = [
    { value: "handoff_or_book", label: "Handoff or Book Appointment" },
    { value: "advise_emergency_and_handoff", label: "Advise Emergency & Handoff" },
    { value: "handoff_only", label: "Handoff Only" },
    { value: "continue_with_warning", label: "Continue with Warning" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Escalation Rules
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Configure escalation policies. The AI will automatically detect when to escalate based on context - no keywords needed.
        </p>
      </div>

      <div className="space-y-6">
        <Select
          label="Medical Question Policy"
          value={config.medical_question_policy || "handoff_or_book"}
          onChange={(e) =>
            onUpdate({ medical_question_policy: e.target.value })
          }
          options={policyOptions}
          helperText="How to handle medical questions that require human expertise"
        />

        <Select
          label="Urgent Case Policy"
          value={config.urgent_case_policy || "advise_emergency_and_handoff"}
          onChange={(e) => onUpdate({ urgent_case_policy: e.target.value })}
          options={policyOptions}
          helperText="How to handle urgent or emergency cases"
        />

        <Select
          label="Repeat Patient Policy"
          value={config.repeat_patient_policy || "handoff_only"}
          onChange={(e) => onUpdate({ repeat_patient_policy: e.target.value })}
          options={policyOptions}
          helperText="How to handle returning patients"
        />

        <Select
          label="Pre-Procedure Policy"
          value={config.pre_procedure_policy || "handoff_only"}
          onChange={(e) => onUpdate({ pre_procedure_policy: e.target.value })}
          options={policyOptions}
          helperText="How to handle pre-procedure questions"
        />
      </div>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-sm">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> The AI will automatically detect escalation triggers based on conversation context. 
          No manual keyword configuration is needed - GPT understands medical questions, urgent cases, and booking intents automatically.
        </p>
      </div>
    </div>
  );
};
