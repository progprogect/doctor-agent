/** Chat page for specific agent. */

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { api, ApiError } from "@/lib/api";
import type { Agent } from "@/lib/types/agent";
import type { Conversation } from "@/lib/types/conversation";

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.agentId as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAgentAndConversation = async () => {
      try {
        setIsLoading(true);

        // Load agent
        const agentData = await api.getAgent(agentId);
        setAgent(agentData);

        // Try to find existing conversation or create new one
        try {
          const conversations = await api.listConversations({
            agent_id: agentId,
            status: "AI_ACTIVE",
            limit: 1,
          });

          if (conversations.length > 0) {
            setConversation(conversations[0]);
          } else {
            // Create new conversation
            const newConversation = await api.createConversation({
              agent_id: agentId,
            });
            setConversation({
              conversation_id: newConversation.conversation_id,
              agent_id: newConversation.agent_id,
              status: newConversation.status as any,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            });
          }
        } catch (err) {
          // Create new conversation if listing fails
          const newConversation = await api.createConversation({
            agent_id: agentId,
          });
          setConversation({
            conversation_id: newConversation.conversation_id,
            agent_id: newConversation.agent_id,
            status: newConversation.status as any,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          });
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load chat");
        }
      } finally {
        setIsLoading(false);
      }
    };

    if (agentId) {
      loadAgentAndConversation();
    }
  }, [agentId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go back
          </button>
        </div>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Failed to create conversation</p>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      <div className="border-b border-gray-200 px-6 py-4 bg-white">
        <h1 className="text-xl font-semibold text-gray-900">
          {agent?.config.profile.clinic_display_name || "Chat"}
        </h1>
        <p className="text-sm text-gray-600">
          {agent?.config.profile.doctor_display_name || ""}
        </p>
      </div>
      <div className="flex-1 overflow-hidden">
        <ChatWindow conversationId={conversation.conversation_id} />
      </div>
    </div>
  );
}

