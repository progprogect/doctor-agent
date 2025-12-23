/** Hook for managing conversation state. */

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Conversation } from "@/lib/types/conversation";

export function useConversation(conversationId: string | null) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConversation = async () => {
    if (!conversationId) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const data = await api.getConversation(conversationId);
      setConversation(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load conversation");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!conversationId) {
      return;
    }

    loadConversation();
    // Poll for status updates every 5 seconds
    const interval = setInterval(() => {
      loadConversation();
    }, 5000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  return {
    conversation,
    isLoading,
    error,
    refresh: loadConversation,
  };
}

