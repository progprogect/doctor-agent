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
    <div className="flex justify-start mb-4">
      <div className="bg-gray-200 rounded-lg px-4 py-2">
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
          <div
            className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
            style={{ animationDelay: "0.1s" }}
          />
          <div
            className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
            style={{ animationDelay: "0.2s" }}
          />
        </div>
      </div>
    </div>
  );
};

