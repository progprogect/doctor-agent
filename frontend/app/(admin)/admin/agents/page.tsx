/** Agents management page. */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/shared/Button";
import type { Agent } from "@/lib/types/agent";

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setIsLoading(true);
      const agentsData = await api.listAgents();
      setAgents(agentsData);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load agents");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAgent = () => {
    router.push("/admin/agents/create");
  };

  const handleCloneAgent = async (agent: Agent) => {
    try {
      // Convert agent config to form data and save to localStorage
      const { agentConfigToFormData } = await import("@/lib/utils/agentConfig");
      const formData = agentConfigToFormData(agent.config);
      
      // Generate new agent_id
      const newAgentId = `${agent.agent_id}_clone_${Date.now()}`;
      formData.agent_id = newAgentId;

      // Save as draft
      const draft = {
        currentStep: 1,
        config: formData,
        timestamp: Date.now(),
        isClone: true,
        sourceAgentId: agent.agent_id,
      };
      localStorage.setItem("agent_wizard_draft", JSON.stringify(draft));

      // Navigate to create page
      router.push("/admin/agents/create");
    } catch (err) {
      console.error("Failed to clone agent:", err);
      setError("Failed to clone agent. Please try again.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
        <Button variant="primary" onClick={handleCreateAgent}>
          Create Agent
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded-sm">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {agents.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-sm shadow border border-[#D4AF37]/20">
          <div className="max-w-md mx-auto">
            <div className="text-6xl mb-4">👨‍⚕️</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No agents yet
            </h2>
            <p className="text-gray-600 mb-6">
              Create your first AI agent to start chatting with patients.
            </p>
            <Button variant="primary" onClick={handleCreateAgent}>
              Create Your First Agent
            </Button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-sm shadow border border-[#D4AF37]/20 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-[#F5D76E]/10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Agent ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {agents.map((agent) => (
                <tr key={agent.agent_id} className="hover:bg-[#F5D76E]/5 transition-colors duration-150">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {agent.agent_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {agent.config.profile?.doctor_display_name || "-"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-sm ${
                        agent.is_active
                          ? "bg-[#F5D76E]/20 text-[#B8860B] border border-[#D4AF37]/30"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {agent.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => handleCloneAgent(agent)}
                      className="text-[#D4AF37] hover:text-[#B8860B] mr-4 transition-colors duration-200"
                      title="Clone this agent"
                    >
                      Clone
                    </button>
                    <button className="text-[#D4AF37] hover:text-[#B8860B] mr-4 transition-colors duration-200">
                      Edit
                    </button>
                    <button className="text-red-600 hover:text-red-700 transition-colors duration-200">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}



