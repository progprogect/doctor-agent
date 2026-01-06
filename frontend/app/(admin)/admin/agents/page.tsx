/** Agents management page. */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/shared/Button";
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import { agentConfigToFormData } from "@/lib/utils/agentConfig";
import type { Agent } from "@/lib/types/agent";

function AgentRow({
  agent,
  onClone,
  onEdit,
  onDelete,
}: {
  agent: Agent;
  onClone: (agent: Agent) => void;
  onEdit: (agent: Agent) => void;
  onDelete: (agent: Agent) => void;
}) {
  const [channelCount, setChannelCount] = useState<number | null>(null);
  const [isLoadingChannels, setIsLoadingChannels] = useState(true);

  useEffect(() => {
    loadChannelCount();
  }, [agent.agent_id]);

  const loadChannelCount = async () => {
    try {
      const bindings = await api.listChannelBindings(agent.agent_id, undefined, false);
      setChannelCount(bindings.length);
    } catch (err) {
      setChannelCount(0);
    } finally {
      setIsLoadingChannels(false);
    }
  };

  return (
    <tr className="hover:bg-[#F5D76E]/5 transition-colors duration-150">
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
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {isLoadingChannels ? (
          <span className="text-gray-400">Loading...</span>
        ) : (
          <Link
            href={`/admin/agents/${agent.agent_id}/channels`}
            className="text-[#D4AF37] hover:text-[#B8860B] transition-colors duration-200"
          >
            {channelCount ?? 0} channel{channelCount !== 1 ? "s" : ""}
          </Link>
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        <button
          onClick={() => onClone(agent)}
          className="text-[#D4AF37] hover:text-[#B8860B] mr-4 transition-colors duration-200 cursor-pointer"
          title="Clone this agent"
        >
          Clone
        </button>
        <button
          onClick={() => onEdit(agent)}
          className="text-[#D4AF37] hover:text-[#B8860B] mr-4 transition-colors duration-200 cursor-pointer"
          title="Edit this agent"
        >
          Edit
        </button>
        <button
          onClick={() => onDelete(agent)}
          className="text-red-600 hover:text-red-700 transition-colors duration-200 cursor-pointer"
          title="Delete this agent"
        >
          Delete
        </button>
      </td>
    </tr>
  );
}

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<Agent | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

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

  const handleEditAgent = async (agent: Agent) => {
    try {
      // Convert agent config to form data and save to localStorage
      const formData = agentConfigToFormData(agent.config);
      
      // Keep the original agent_id for editing
      formData.agent_id = agent.agent_id;

      // Save as draft with edit flag
      const draft = {
        currentStep: 1,
        config: formData,
        timestamp: Date.now(),
        isEdit: true,
        editingAgentId: agent.agent_id,
      };
      localStorage.setItem("agent_wizard_draft", JSON.stringify(draft));

      // Navigate to create page (which handles both create and edit)
      router.push("/admin/agents/create");
    } catch (err) {
      console.error("Failed to load agent for editing:", err);
      setError("Failed to load agent for editing. Please try again.");
    }
  };

  const handleDeleteAgent = (agent: Agent) => {
    setAgentToDelete(agent);
    setIsDeleteModalOpen(true);
  };

  const confirmDeleteAgent = async () => {
    if (!agentToDelete) return;

    try {
      setIsDeleting(true);
      setError(null);
      
      await api.deleteAgent(agentToDelete.agent_id);
      
      // Remove agent from list
      setAgents(agents.filter((a) => a.agent_id !== agentToDelete.agent_id));
      
      // Close modal
      setIsDeleteModalOpen(false);
      setAgentToDelete(null);
    } catch (err) {
      console.error("Failed to delete agent:", err);
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to delete agent. Please try again.");
      }
    } finally {
      setIsDeleting(false);
    }
  };

  const closeDeleteModal = () => {
    if (!isDeleting) {
      setIsDeleteModalOpen(false);
      setAgentToDelete(null);
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
                  Channels
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {agents.map((agent) => (
                <AgentRow
                  key={agent.agent_id}
                  agent={agent}
                  onClone={handleCloneAgent}
                  onEdit={handleEditAgent}
                  onDelete={handleDeleteAgent}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={closeDeleteModal}
        onConfirm={confirmDeleteAgent}
        title="Delete Agent"
        message={
          agentToDelete
            ? `Are you sure you want to delete agent "${agentToDelete.config.profile?.doctor_display_name || agentToDelete.agent_id}"?\n\nThis action will deactivate the agent. This action cannot be undone.`
            : ""
        }
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}



