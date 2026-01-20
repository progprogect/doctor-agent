/** Conversation detail page. */

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/shared/Button";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { MessageInput } from "@/components/chat/MessageInput";
import { useConversation } from "@/lib/hooks/useConversation";
import { useMessages } from "@/lib/hooks/useMessages";
import { useAdminWebSocket } from "@/lib/hooks/useAdminWebSocket";
import { handleApiError, getUserFriendlyMessage } from "@/lib/errorHandler";
import type { Conversation } from "@/lib/types/conversation";
import type { Message } from "@/lib/types/message";
import { getChannelDisplay, isInstagramChannel } from "@/lib/utils/channelDisplay";

export default function ConversationDetailPage() {
  const params = useParams();
  const conversationId = params.id as string;

  const {
    conversation,
    isLoading: conversationLoading,
    isRefreshing: conversationRefreshing,
    error: conversationError,
    refresh: refreshConversation,
  } = useConversation(conversationId);

  const {
    messages,
    isLoading: messagesLoading,
    isRefreshing: messagesRefreshing,
    error: messagesError,
    refresh: refreshMessages,
  } = useMessages(conversationId, true);

  const { onConversationUpdate } = useAdminWebSocket();
  const [actionError, setActionError] = useState<string | null>(null);
  const isLoading = conversationLoading || messagesLoading;
  const isRefreshing = conversationRefreshing || messagesRefreshing;
  const error = conversationError || messagesError || actionError;

  // Listen for WebSocket updates for this conversation
  useEffect(() => {
    const unsubscribe = onConversationUpdate((updatedConversation: Conversation) => {
      if (updatedConversation.conversation_id === conversationId) {
        refreshConversation();
        refreshMessages();
      }
    });

    return unsubscribe;
  }, [conversationId, onConversationUpdate, refreshConversation, refreshMessages]);

  const handleHandoff = async () => {
    try {
      setActionError(null);
      await api.handoffConversation(conversationId, "admin_user", "Manual handoff");
      await refreshConversation();
      await refreshMessages();
    } catch (err) {
      const errorInfo = handleApiError(err);
      setActionError(getUserFriendlyMessage(errorInfo));
    }
  };

  const handleReturnToAI = async () => {
    try {
      setActionError(null);
      await api.returnToAI(conversationId, "admin_user");
      await refreshConversation();
      await refreshMessages();
    } catch (err) {
      const errorInfo = handleApiError(err);
      setActionError(getUserFriendlyMessage(errorInfo));
    }
  };

  const handleSendAdminMessage = async (content: string) => {
    try {
      setActionError(null);
      await api.sendAdminMessage(conversationId, "admin_user", content);
      await refreshMessages();
    } catch (err) {
      const errorInfo = handleApiError(err);
      setActionError(getUserFriendlyMessage(errorInfo));
    }
  };

  const canSendAdminMessage =
    conversation?.status === "NEEDS_HUMAN" ||
    conversation?.status === "HUMAN_ACTIVE";

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4">
        <p className="text-sm text-red-700">{error || "Conversation not found"}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Conversation</h1>
          <p className="text-sm text-gray-600 mt-1">
            {conversation.conversation_id}
          </p>
        </div>
        <div className="flex gap-2">
          {conversation.status === "AI_ACTIVE" && (
            <Button variant="primary" onClick={handleHandoff}>
              Handoff to Human
            </Button>
          )}
          {conversation.status === "HUMAN_ACTIVE" && (
            <Button variant="secondary" onClick={handleReturnToAI}>
              Return to AI
            </Button>
          )}
        </div>
      </div>

      {actionError && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded-sm">
          <p className="text-sm text-red-700">{actionError}</p>
        </div>
      )}

      <div className="bg-white rounded-sm shadow border border-[#D4AF37]/20 p-6 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="text-sm font-medium text-gray-900">{conversation.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Agent ID</p>
            <p className="text-sm font-medium text-gray-900">{conversation.agent_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Channel</p>
            <p className="text-sm font-medium text-gray-900">
              {getChannelDisplay(conversation.channel)}
            </p>
          </div>
          {isInstagramChannel(conversation.channel) && (
            <>
              {conversation.external_user_id && (
                <div>
                  <p className="text-sm text-gray-500">Instagram User ID</p>
                  <p className="text-sm font-medium text-gray-900">{conversation.external_user_id}</p>
                </div>
              )}
              {conversation.external_conversation_id && (
                <div>
                  <p className="text-sm text-gray-500">Instagram Thread ID</p>
                  <p className="text-sm font-medium text-gray-900">{conversation.external_conversation_id}</p>
                </div>
              )}
            </>
          )}
          {conversation.handoff_reason && (
            <div>
              <p className="text-sm text-gray-500">Handoff Reason</p>
              <p className="text-sm font-medium text-gray-900">
                {conversation.handoff_reason}
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-sm shadow border border-[#D4AF37]/20 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Messages</h2>
        <div className="space-y-4 mb-4">
          {messages.length === 0 ? (
            <p className="text-gray-600 text-center py-8">No messages yet</p>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.message_id} message={message} />
            ))
          )}
        </div>

        {canSendAdminMessage && (
          <div className="border-t border-gray-200 pt-4 mt-4">
            <MessageInput
              onSend={handleSendAdminMessage}
              placeholder="Type your message as admin..."
              disabled={false}
            />
          </div>
        )}
      </div>
    </div>
  );
}

