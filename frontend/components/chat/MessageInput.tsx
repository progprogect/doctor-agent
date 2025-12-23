/** Message input component. */

import React, { useState, KeyboardEvent } from "react";
import { Button } from "@/components/shared/Button";

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  onSend,
  disabled = false,
  placeholder = "Type your message...",
}) => {
  const [content, setContent] = useState("");

  const handleSend = () => {
    if (content.trim() && !disabled) {
      onSend(content);
      setContent("");
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 p-4">
      <div className="flex gap-2">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          placeholder={placeholder}
          rows={1}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <Button
          onClick={handleSend}
          disabled={disabled || !content.trim()}
          variant="primary"
        >
          Send
        </Button>
      </div>
    </div>
  );
};

