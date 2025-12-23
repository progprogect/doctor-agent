/** Hook for managing messages. */

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Message } from "@/lib/types/message";

export function useMessages(conversationId: string | null, autoRefresh = false) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMessages = async () => {
    if (!conversationId) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const data = await api.getMessages(conversationId);
      setMessages(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load messages");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!conversationId) {
      return;
    }

    loadMessages();

    if (autoRefresh) {
      // Poll for new messages every 3 seconds
      const interval = setInterval(() => {
        loadMessages();
      }, 3000);

      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId, autoRefresh]);

  return {
    messages,
    isLoading,
    error,
    refresh: loadMessages,
  };
}

