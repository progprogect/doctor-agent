/** Conversations monitoring page with real-time updates. */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useConversationsList, type ConversationFilter } from "@/lib/hooks/useConversationsList";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/shared/Button";
import { Select } from "@/components/shared/Select";
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import { api } from "@/lib/api";
import Link from "next/link";
import type { Conversation } from "@/lib/types/conversation";

export default function ConversationsPage() {
  const router = useRouter();
  const [filter, setFilter] = useState<ConversationFilter>("all");
  const [takeOverConversationId, setTakeOverConversationId] = useState<string | null>(null);
  const [isTakingOver, setIsTakingOver] = useState(false);

  const {
    conversations,
    isLoading,
    error,
    needsHumanCount,
    isConnected,
    refresh,
  } = useConversationsList({
    filter,
    limit: 100,
    enablePolling: true,
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "AI_ACTIVE":
        return "bg-[#F5D76E]/20 text-[#B8860B] border border-[#D4AF37]/30";
      case "NEEDS_HUMAN":
        return "bg-[#F59E0B]/20 text-[#D97706] border border-[#F59E0B]/30";
      case "HUMAN_ACTIVE":
        return "bg-[#3B82F6]/20 text-[#2563EB] border border-[#3B82F6]/30";
      case "CLOSED":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getWaitingTime = (updatedAt: string): string => {
    const now = new Date();
    const updated = new Date(updatedAt);
    const diffMs = now.getTime() - updated.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m`;
    const diffHours = Math.floor(diffMins / 60);
    return `${diffHours}h`;
  };

  const handleTakeOver = async (conversationId: string) => {
    try {
      setIsTakingOver(true);
      await api.handoffConversation(conversationId, "admin_user", "Quick takeover");
      setTakeOverConversationId(null);
      // Refresh to get updated status
      await refresh();
      // Optionally redirect to conversation detail page
      router.push(`/admin/conversations/${conversationId}`);
    } catch (err) {
      console.error("Failed to take over conversation:", err);
      alert("Failed to take over conversation. Please try again.");
    } finally {
      setIsTakingOver(false);
    }
  };

  const isNeedsHuman = (status: string) => status === "NEEDS_HUMAN";

  if (isLoading && conversations.length === 0) {
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
          <h1 className="text-2xl font-bold text-gray-900">Conversations</h1>
          <p className="text-sm text-gray-600 mt-1">
            {needsHumanCount > 0 && (
              <span className="text-[#F59E0B] font-medium">
                {needsHumanCount} conversation{needsHumanCount !== 1 ? "s" : ""} require{needsHumanCount === 1 ? "s" : ""} attention
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Connection status indicator */}
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-green-500" : "bg-gray-400"
              }`}
            />
            <span className="text-sm text-gray-600">
              {isConnected ? "Live" : "Polling"}
            </span>
          </div>
          
          {/* Filter dropdown */}
          <div className="w-48">
            <Select
              value={filter}
              onChange={(e) => setFilter(e.target.value as ConversationFilter)}
              options={[
                { value: "all", label: "All Conversations" },
                { value: "needs_attention", label: "Requires Attention" },
                { value: "active", label: "Active" },
                { value: "closed", label: "Closed" },
              ]}
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded-sm">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {conversations.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600">No conversations found</p>
        </div>
      ) : (
        <div className="bg-white rounded-sm shadow border border-[#D4AF37]/20 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-[#F5D76E]/10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Conversation ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Agent ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Created
                </th>
                {filter === "all" || filter === "needs_attention" ? (
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                    Waiting
                  </th>
                ) : null}
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {conversations.map((conv) => {
                const needsAttention = isNeedsHuman(conv.status);
                return (
                  <tr
                    key={conv.conversation_id}
                    className={`transition-colors duration-150 ${
                      needsAttention
                        ? "bg-[#F59E0B]/10 hover:bg-[#F59E0B]/15 border-l-4 border-[#F59E0B]"
                        : "hover:bg-[#F5D76E]/5"
                    }`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {needsAttention && (
                          <span className="text-lg" title="Requires attention">
                            ⚠️
                          </span>
                        )}
                        <span
                          className={`text-sm ${
                            needsAttention ? "font-bold text-gray-900" : "font-medium text-gray-900"
                          }`}
                        >
                          {conv.conversation_id.substring(0, 8)}...
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {conv.agent_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-sm ${getStatusColor(
                          conv.status
                        )}`}
                      >
                        {conv.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(conv.created_at).toLocaleDateString()}
                    </td>
                    {(filter === "all" || filter === "needs_attention") && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {needsAttention ? (
                          <span className="text-[#F59E0B] font-medium">
                            {getWaitingTime(conv.updated_at)}
                          </span>
                        ) : (
                          "-"
                        )}
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-3">
                        {needsAttention && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setTakeOverConversationId(conv.conversation_id)}
                            disabled={isTakingOver}
                          >
                            Take Over
                          </Button>
                        )}
                        <Link
                          href={`/admin/conversations/${conv.conversation_id}`}
                          className="text-[#D4AF37] hover:text-[#B8860B] transition-colors duration-200"
                        >
                          View
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Take Over Confirmation Modal */}
      <ConfirmModal
        isOpen={!!takeOverConversationId}
        onClose={() => setTakeOverConversationId(null)}
        onConfirm={() => takeOverConversationId && handleTakeOver(takeOverConversationId)}
        title="Take Over Conversation"
        message="Are you sure you want to take over this conversation? You will be able to respond to the user directly."
        confirmText="Take Over"
        cancelText="Cancel"
        isLoading={isTakingOver}
        variant="warning"
      />
    </div>
  );
}
