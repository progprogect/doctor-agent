/** Typing indicator component with improved animation and text. */

import React from "react";

interface TypingIndicatorProps {
  isTyping: boolean;
  agentName?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  isTyping,
  agentName,
}) => {
  if (!isTyping) {
    return null;
  }

  return (
    <div className="flex items-start gap-2 mb-4 px-4">
      {/* Avatar */}
      <div
        className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-lg bg-[#F5D76E]/20"
        aria-hidden="true"
      >
        🤖
      </div>

      {/* Typing bubble */}
      <div className="bg-white border border-[#D4AF37]/30 rounded-sm px-4 py-3 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div
              className="w-2 h-2 bg-[#D4AF37] rounded-full animate-bounce"
              style={{ animationDuration: "1.4s" }}
            />
            <div
              className="w-2 h-2 bg-[#D4AF37] rounded-full animate-bounce"
              style={{ animationDelay: "0.2s", animationDuration: "1.4s" }}
            />
            <div
              className="w-2 h-2 bg-[#D4AF37] rounded-full animate-bounce"
              style={{ animationDelay: "0.4s", animationDuration: "1.4s" }}
            />
          </div>
          <span className="text-xs text-gray-500 ml-1">
            {agentName ? `${agentName} is typing...` : "Agent is typing..."}
          </span>
        </div>
      </div>
    </div>
  );
};



