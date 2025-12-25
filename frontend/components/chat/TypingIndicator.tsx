/** Typing indicator component. */

import React from "react";

interface TypingIndicatorProps {
  isTyping: boolean;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  isTyping,
}) => {
  if (!isTyping) {
    return null;
  }

  return (
    <div className="flex justify-start mb-4 px-4">
      <div className="bg-white border border-[#D4AF37]/30 rounded-sm px-4 py-2">
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-[#D4AF37] rounded-full animate-bounce" />
          <div
            className="w-2 h-2 bg-[#D4AF37] rounded-full animate-bounce"
            style={{ animationDelay: "0.1s" }}
          />
          <div
            className="w-2 h-2 bg-[#D4AF37] rounded-full animate-bounce"
            style={{ animationDelay: "0.2s" }}
          />
        </div>
      </div>
    </div>
  );
};



