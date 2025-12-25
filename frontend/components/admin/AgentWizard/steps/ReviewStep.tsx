/** Step 6: Review and Create. */

"use client";

import React, { useState, useMemo } from "react";
import { Button } from "@/components/shared/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { YAMLEditor } from "@/components/shared/YAMLEditor";
import { api, ApiError } from "@/lib/api";
import type { AgentConfigFormData } from "@/lib/utils/agentConfig";
import { formDataToAgentConfig } from "@/lib/utils/agentConfig";

interface ReviewStepProps {
  config: Partial<AgentConfigFormData>;
  isSubmitting?: boolean;
  onSubmit: () => Promise<void> | void;
}

export const ReviewStep: React.FC<ReviewStepProps> = ({
  config,
  isSubmitting: externalIsSubmitting,
  onSubmit,
}) => {
  const [error, setError] = useState<string | null>(null);
  const [yamlPreview, setYamlPreview] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editMode, setEditMode] = useState<"form" | "yaml">("form");
  const [editedConfig, setEditedConfig] = useState<Record<string, any> | null>(
    null
  );
  const [jsonError, setJsonError] = useState<string | null>(null);

  // Generate YAML preview
  const agentConfig = useMemo(() => {
    return editedConfig || formDataToAgentConfig(config as AgentConfigFormData);
  }, [config, editedConfig]);

  React.useEffect(() => {
    try {
      // Convert to YAML-like format (JSON with proper indentation)
      const yaml = JSON.stringify(agentConfig, null, 2);
      setYamlPreview(yaml);
    } catch {
      setYamlPreview("Error generating preview");
    }
  }, [agentConfig]);

  const handleCreate = async () => {
    if (!config.agent_id) {
      setError("Agent ID is required");
      return;
    }

    // Validate JSON if in YAML edit mode
    if (editMode === "yaml") {
      if (!editedConfig || jsonError) {
        setError("Invalid JSON configuration. Please fix the errors before creating the agent.");
        return;
      }
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Use edited config if in YAML mode, otherwise use form data
      const agentConfig =
        editMode === "yaml" && editedConfig
          ? editedConfig
          : formDataToAgentConfig(config as AgentConfigFormData);

      // Validate agent_id matches
      if (agentConfig.agent_id !== config.agent_id) {
        agentConfig.agent_id = config.agent_id;
      }

      await api.createAgent(config.agent_id, agentConfig);
      // Call onSubmit to trigger success handler in parent
      await onSubmit();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to create agent. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleYAMLChange = (value: string) => {
    try {
      const parsed = JSON.parse(value);
      setEditedConfig(parsed);
      setJsonError(null);
      setError(null);
    } catch (e) {
      // Invalid JSON - keep the value but show error
      setEditedConfig(null);
      setJsonError("Invalid JSON syntax");
    }
  };

  const submitting = isSubmitting || externalIsSubmitting;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Review Configuration
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Review your agent configuration before creating.
        </p>
      </div>

      {/* Summary */}
      <div className="bg-gray-50 rounded-sm border border-gray-200 p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Summary</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Agent ID:</span>
            <span className="font-medium text-gray-900">
              {config.agent_id || "Not set"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Clinic:</span>
            <span className="font-medium text-gray-900">
              {config.clinic_display_name || "Not set"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Doctor:</span>
            <span className="font-medium text-gray-900">
              {config.doctor_display_name || "Not set"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Specialty:</span>
            <span className="font-medium text-gray-900">
              {config.specialty || "Not set"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">RAG Enabled:</span>
            <span className="font-medium text-gray-900">
              {config.rag_enabled ? "Yes" : "No"}
            </span>
          </div>
          {config.rag_enabled && (
            <div className="flex justify-between">
              <span className="text-gray-600">RAG Documents:</span>
              <span className="font-medium text-gray-900">
                {config.rag_documents?.length || 0}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* YAML/JSON Editor */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-md font-medium text-gray-900">
            Configuration Preview
          </h4>
          <div className="flex gap-2">
            <Button
              variant={editMode === "form" ? "primary" : "secondary"}
              size="sm"
              onClick={() => {
                setEditMode("form");
                setEditedConfig(null);
                setJsonError(null);
              }}
            >
              Form View
            </Button>
            <Button
              variant={editMode === "yaml" ? "primary" : "secondary"}
              size="sm"
              onClick={() => {
                setEditMode("yaml");
                // Reset JSON error when switching to YAML mode
                setJsonError(null);
              }}
            >
              JSON Editor
            </Button>
          </div>
        </div>
        {editMode === "yaml" ? (
          <YAMLEditor
            value={yamlPreview}
            onChange={handleYAMLChange}
            readOnly={false}
            height="500px"
            language="json"
            error={jsonError || undefined}
          />
        ) : (
          <div className="border border-gray-300 rounded-sm p-4 bg-gray-50 max-h-[500px] overflow-auto">
            <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
              {yamlPreview}
            </pre>
          </div>
        )}
        {editMode === "yaml" && (
          <p className="mt-2 text-xs text-gray-500">
            You can edit the JSON configuration directly. Changes will be applied when you create the agent.
          </p>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-sm">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {submitting && (
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600">
            Creating agent and indexing documents...
          </span>
        </div>
      )}

      {/* Create Button */}
      {!submitting && (
        <div className="flex justify-end">
          <Button variant="primary" onClick={handleCreate} size="lg">
            Create Agent
          </Button>
        </div>
      )}
    </div>
  );
};

