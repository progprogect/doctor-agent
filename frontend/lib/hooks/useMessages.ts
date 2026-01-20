/** Hook for managing messages. */

import { useEffect, useState, useRef } from "react";
import { api, ApiError } from "@/lib/api";
import type { Message } from "@/lib/types/message";

export function useMessages(conversationId: string | null, autoRefresh = false) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isInitialLoadRef = useRef(true);

  const loadMessages = async (isPolling = false) => {
    if (!conversationId) {
      return;
    }

    try {
      // Only set isLoading for initial load, not for polling
      if (isInitialLoadRef.current && !isPolling) {
        setIsLoading(true);
      } else if (isPolling) {
        setIsRefreshing(true);
      }
      setError(null);
      const data = await api.getMessages(conversationId);
      setMessages(data);
      isInitialLoadRef.current = false;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load messages");
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (!conversationId) {
      return;
    }

    isInitialLoadRef.current = true;
    loadMessages(false);

    if (autoRefresh) {
      // Poll for new messages every 5 seconds (less aggressive)
      const interval = setInterval(() => {
        loadMessages(true);
      }, 5000);

      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId, autoRefresh]);

  return {
    messages,
    isLoading,
    isRefreshing,
    error,
    refresh: () => loadMessages(false),
  };
}

