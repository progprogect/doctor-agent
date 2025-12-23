/** Main chat window component. */

"use client";

import React from "react";
import { useChat } from "@/lib/hooks/useChat";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { TypingIndicator } from "./TypingIndicator";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

interface ChatWindowProps {
  conversationId: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ conversationId }) => {
  const {
    messages,
    isLoading,
    error,
    isTyping,
    isConnected,
    sendMessage,
    messagesEndRef,
  } = useChat(conversationId);

  if (isLoading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Connection status */}
      <div className="border-b border-gray-200 px-4 py-2 bg-gray-50">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 m-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Messages */}
      <MessageList messages={messages} messagesEndRef={messagesEndRef} />

      {/* Typing indicator */}
      <TypingIndicator isTyping={isTyping} />

      {/* Input */}
      <MessageInput
        onSend={sendMessage}
        disabled={!isConnected || isLoading}
      />
    </div>
  );
};

