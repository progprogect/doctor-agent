/** Message bubble component. */

import React from "react";
import type { Message } from "@/lib/types/message";

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";
  const isAdmin = message.role === "admin";

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
    >
      <div
        className={`max-w-[70%] rounded-sm px-4 py-2 transition-all duration-200 ${
          isUser
            ? "bg-[#D4AF37] text-white shadow-sm"
            : isAdmin
            ? "bg-[#B8860B] text-white shadow-sm"
            : "bg-white text-gray-900 border border-[#D4AF37]/30"
        }`}
      >
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>
        <p
          className={`text-xs mt-1 ${
            isUser ? "text-white/80" : "text-gray-500"
          }`}
        >
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  );
};



