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
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/126a4647-5038-49ca-aac8-2a19a486f321',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useMessages.ts:27',message:'Before api.getMessages',data:{conversationId,isPolling},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C,D'})}).catch(()=>{});
      // #endregion
      const data = await api.getMessages(conversationId);
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/126a4647-5038-49ca-aac8-2a19a486f321',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useMessages.ts:30',message:'After api.getMessages',data:{conversationId,count:Array.isArray(data)?data.length:0,messageIds:Array.isArray(data)?data.slice(0,5).map(m=>m.message_id):[],roles:Array.isArray(data)?data.slice(0,5).map(m=>m.role):[]},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C,D,E'})}).catch(()=>{});
      // #endregion
      // Ensure we always have an array, even if API returns null/undefined
      const messagesArray = Array.isArray(data) ? data : [];
      setMessages(messagesArray);
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/126a4647-5038-49ca-aac8-2a19a486f321',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useMessages.ts:34',message:'setMessages called',data:{conversationId,count:messagesArray.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
      isInitialLoadRef.current = false;
    } catch (err) {
      // Don't show error for polling failures, only for initial load
      if (isInitialLoadRef.current && !isPolling) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load messages");
        }
      } else {
        // For polling errors, just log them silently
        console.warn("Failed to refresh messages:", err);
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
    setMessages: setMessages,
  };
}

