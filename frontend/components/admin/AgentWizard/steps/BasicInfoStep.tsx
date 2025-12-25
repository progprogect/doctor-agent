/** Step 1: Basic Information. */

"use client";

import React, { useEffect } from "react";
import { Input } from "@/components/shared/Input";
import type { AgentConfigFormData } from "@/lib/utils/agentConfig";
import type { ValidationError } from "@/lib/utils/validation";
import { getFieldError } from "@/lib/utils/validation";
import { generateAgentId } from "@/lib/utils/agentConfig";

interface BasicInfoStepProps {
  config: Partial<AgentConfigFormData>;
  errors: ValidationError[];
  onUpdate: (config: Partial<AgentConfigFormData>) => void;
}

export const BasicInfoStep: React.FC<BasicInfoStepProps> = ({
  config,
  errors,
  onUpdate,
}) => {
  // Auto-generate agent_id when clinic_display_name changes
  useEffect(() => {
    if (
      config.clinic_display_name &&
      !config.agent_id &&
      config.clinic_display_name.trim() !== ""
    ) {
      const generatedId = generateAgentId(config.clinic_display_name);
      onUpdate({ agent_id: generatedId });
    }
  }, [config.clinic_display_name, config.agent_id, onUpdate]);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Basic Information
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Provide basic information about the doctor and clinic.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="md:col-span-2">
          <Input
            label="Clinic Display Name"
            value={config.clinic_display_name || ""}
            onChange={(e) =>
              onUpdate({ clinic_display_name: e.target.value })
            }
            error={getFieldError(errors, "clinic_display_name")}
            placeholder="Elemental Clinic"
            required
          />
        </div>

        <div className="md:col-span-2">
          <Input
            label="Doctor Display Name"
            value={config.doctor_display_name || ""}
            onChange={(e) => onUpdate({ doctor_display_name: e.target.value })}
            error={getFieldError(errors, "doctor_display_name")}
            placeholder="Dr. [Имя Фамилия]"
            required
          />
        </div>

        <div className="md:col-span-2">
          <Input
            label="Specialty"
            value={config.specialty || ""}
            onChange={(e) => onUpdate({ specialty: e.target.value })}
            error={getFieldError(errors, "specialty")}
            placeholder="General Practitioner"
            required
          />
        </div>

        <div className="md:col-span-2">
          <Input
            label="Agent ID"
            value={config.agent_id || ""}
            onChange={(e) => onUpdate({ agent_id: e.target.value })}
            error={getFieldError(errors, "agent_id")}
            placeholder="doctor_001"
            required
            helperText="Auto-generated from clinic name. Must contain only lowercase letters, numbers, and underscores."
          />
        </div>
      </div>

      {/* Preview Card */}
      {(config.clinic_display_name ||
        config.doctor_display_name ||
        config.specialty) && (
        <div className="mt-8 p-6 bg-[#F5D76E]/10 border border-[#D4AF37]/20 rounded-sm">
          <h4 className="text-sm font-medium text-gray-700 mb-4">Preview</h4>
          <div className="bg-white p-4 rounded-sm border border-[#D4AF37]/20">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h5 className="text-lg font-semibold text-gray-900">
                  {config.clinic_display_name || "Clinic Name"}
                </h5>
                {config.doctor_display_name && (
                  <p className="text-sm text-gray-600">
                    {config.doctor_display_name}
                  </p>
                )}
              </div>
              <div className="text-3xl">👨‍⚕️</div>
            </div>
            {config.specialty && (
              <p className="text-sm text-gray-500">{config.specialty}</p>
            )}
            <div className="mt-3">
              <span className="px-3 py-1 rounded-sm text-xs font-medium bg-[#F5D76E]/20 text-[#B8860B] border border-[#D4AF37]/30">
                Active
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

