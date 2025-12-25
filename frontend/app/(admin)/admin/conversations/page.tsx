/** Conversations monitoring page. */

"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import Link from "next/link";
import type { Conversation } from "@/lib/types/conversation";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConversations();
    // Refresh every 5 seconds
    const interval = setInterval(loadConversations, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadConversations = async () => {
    try {
      const data = await api.listConversations({ limit: 100 });
      setConversations(data);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load conversations");
      }
    } finally {
      setIsLoading(false);
    }
  };

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

  if (isLoading && conversations.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Conversations</h1>

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
                <th className="px-6 py-3 text-left text-xs font-medium text-[#B8860B] uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {conversations.map((conv) => (
                <tr key={conv.conversation_id} className="hover:bg-[#F5D76E]/5 transition-colors duration-150">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {conv.conversation_id.substring(0, 8)}...
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Link
                      href={`/admin/conversations/${conv.conversation_id}`}
                      className="text-[#D4AF37] hover:text-[#B8860B] transition-colors duration-200"
                    >
                      View
                    </Link>
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



