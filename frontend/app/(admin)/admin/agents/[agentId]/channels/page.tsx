/** Channel bindings management page for an agent. */

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/shared/Button";
import type { ChannelBinding, ChannelType } from "@/lib/types/channel";
import { ChannelBindingsList } from "@/components/admin/ChannelBindingsList";
import { ChannelBindingModal } from "@/components/admin/ChannelBindingModal";

export default function AgentChannelsPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.agentId as string;

  const [bindings, setBindings] = useState<ChannelBinding[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [channelType, setChannelType] = useState<ChannelType | null>(null);

  useEffect(() => {
    if (agentId) {
      loadBindings();
    }
  }, [agentId]);

  const loadBindings = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const bindingsData = await api.listChannelBindings(agentId);
      setBindings(bindingsData);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load channel bindings");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateBinding = (type: ChannelType) => {
    setChannelType(type);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setChannelType(null);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    setChannelType(null);
    loadBindings();
  };

  const handleDeleteBinding = async (bindingId: string) => {
    if (!confirm("Are you sure you want to delete this channel binding?")) {
      return;
    }

    try {
      await api.deleteChannelBinding(bindingId);
      setBindings(bindings.filter((b) => b.binding_id !== bindingId));
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to delete channel binding");
      }
    }
  };

  const handleToggleActive = async (bindingId: string, isActive: boolean) => {
    try {
      const updated = await api.updateChannelBinding(bindingId, {
        is_active: !isActive,
      });
      setBindings(
        bindings.map((b) => (b.binding_id === bindingId ? updated : b))
      );
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to update channel binding");
      }
    }
  };

  const handleVerify = async (bindingId: string) => {
    try {
      const result = await api.verifyChannelBinding(bindingId);
      if (result.is_verified) {
        await loadBindings();
      } else {
        setError("Token verification failed");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to verify channel binding");
      }
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
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Channel Bindings
          </h1>
          <p className="text-sm text-gray-600 mt-1">Agent: {agentId}</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="primary"
            onClick={() => handleCreateBinding("instagram" as ChannelType)}
          >
            Connect Instagram
          </Button>
          <Button
            variant="primary"
            onClick={() => handleCreateBinding("telegram" as ChannelType)}
          >
            Connect Telegram
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded-sm">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <ChannelBindingsList
        bindings={bindings}
        onDelete={handleDeleteBinding}
        onToggleActive={handleToggleActive}
        onVerify={handleVerify}
      />

      {isModalOpen && channelType && (
        <ChannelBindingModal
          agentId={agentId}
          channelType={channelType}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  );
}

