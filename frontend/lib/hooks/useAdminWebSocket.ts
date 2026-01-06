/** Hook for managing admin WebSocket connection. */

import { useEffect, useRef, useState, useCallback } from "react";
import { AdminWebSocketClient, type AdminWebSocketMessage } from "@/lib/adminWebSocket";

export function useAdminWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsClientRef = useRef<AdminWebSocketClient | null>(null);
  const conversationUpdateHandlersRef = useRef<Set<(conversation: any) => void>>(
    new Set()
  );
  const escalationHandlersRef = useRef<Set<(conversation: any, reason?: string) => void>>(
    new Set()
  );
  const statsUpdateHandlersRef = useRef<Set<(stats: any) => void>>(new Set());

  useEffect(() => {
    const client = new AdminWebSocketClient();
    wsClientRef.current = client;

    const unsubscribeConnection = client.onConnectionStateChange(setIsConnected);
    const unsubscribeError = client.onError(setError);

    // Handle different message types
    const unsubscribeMessage = client.onMessage((message: AdminWebSocketMessage) => {
      if (message.type === "conversation_updated" && message.conversation) {
        conversationUpdateHandlersRef.current.forEach((handler) => {
          try {
            handler(message.conversation!);
          } catch (err) {
            console.error("Error in conversation update handler:", err);
          }
        });
      } else if (
        message.type === "conversation_escalated" &&
        message.conversation
      ) {
        escalationHandlersRef.current.forEach((handler) => {
          try {
            handler(message.conversation!, message.escalation_reason);
          } catch (err) {
            console.error("Error in escalation handler:", err);
          }
        });
      } else if (message.type === "stats_updated" && message.stats) {
        statsUpdateHandlersRef.current.forEach((handler) => {
          try {
            handler(message.stats!);
          } catch (err) {
            console.error("Error in stats update handler:", err);
          }
        });
      }
    });

    client.connect().catch((err) => {
      setError(err);
    });

    return () => {
      unsubscribeConnection();
      unsubscribeError();
      unsubscribeMessage();
      client.disconnect();
    };
  }, []);

  const onConversationUpdate = useCallback(
    (callback: (conversation: any) => void) => {
      conversationUpdateHandlersRef.current.add(callback);
      return () => {
        conversationUpdateHandlersRef.current.delete(callback);
      };
    },
    []
  );

  const onNewEscalation = useCallback(
    (callback: (conversation: any, reason?: string) => void) => {
      escalationHandlersRef.current.add(callback);
      return () => {
        escalationHandlersRef.current.delete(callback);
      };
    },
    []
  );

  const onStatsUpdate = useCallback((callback: (stats: any) => void) => {
    statsUpdateHandlersRef.current.add(callback);
    return () => {
      statsUpdateHandlersRef.current.delete(callback);
    };
  }, []);

  return {
    isConnected,
    error,
    onConversationUpdate,
    onNewEscalation,
    onStatsUpdate,
  };
}

