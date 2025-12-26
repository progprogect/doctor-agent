/** API client for backend communication. */

import { getAdminToken } from "./auth";
import type {
  Agent,
  CreateConversationRequest,
  CreateConversationResponse,
  Conversation,
  ErrorResponse,
  Message,
  SendMessageRequest,
  SendMessageResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: Record<string, any>,
    public requestId?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  requireAuth: boolean = false
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Add Authorization header for admin endpoints
  if (requireAuth) {
    const token = getAdminToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle empty responses (e.g., 204 No Content)
    if (response.status === 204) {
      return undefined as T;
    }

    // For 201 Created, check if there's a response body
    if (response.status === 201) {
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        try {
          const data = await response.json();
          return data as T;
        } catch {
          // If parsing fails, return undefined
          return undefined as T;
        }
      }
      // If no JSON content type, return undefined
      return undefined as T;
    }

    const data = await response.json();

    if (!response.ok) {
      const error = data as ErrorResponse;
      
      // Handle authentication errors
      if (response.status === 401 || response.status === 403) {
        // Clear token on auth failure
        if (typeof window !== "undefined") {
          localStorage.removeItem("doctor_agent_admin_token");
        }
      }
      
      throw new ApiError(
        error.error.code || "UNKNOWN_ERROR",
        error.error.message || "An error occurred",
        error.error.details,
        error.error.request_id
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      "NETWORK_ERROR",
      error instanceof Error ? error.message : "Network request failed"
    );
  }
}

export const api = {
  // Agent endpoints
  async getAgent(agentId: string): Promise<Agent> {
    return request<Agent>(`/api/v1/agents/${agentId}`);
  },

  async listAgents(activeOnly: boolean = true): Promise<Agent[]> {
    return request<Agent[]>(`/api/v1/agents?active_only=${activeOnly}`);
  },

  async createAgent(agentId: string, config: any): Promise<Agent> {
    return request<Agent>(
      "/api/v1/agents/",
      {
        method: "POST",
        body: JSON.stringify({ agent_id: agentId, config }),
      },
      true // require auth
    );
  },

  async updateAgent(agentId: string, config: any): Promise<Agent> {
    return request<Agent>(
      `/api/v1/agents/${agentId}`,
      {
        method: "PUT",
        body: JSON.stringify(config),
      },
      true // require auth
    );
  },

  async deleteAgent(agentId: string): Promise<void> {
    await request<void>(
      `/api/v1/agents/${agentId}`,
      {
        method: "DELETE",
      },
      true // require auth
    );
  },

  // Conversation endpoints
  async createConversation(
    data: CreateConversationRequest
  ): Promise<CreateConversationResponse> {
    return request<CreateConversationResponse>("/api/v1/chat/conversations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getConversation(conversationId: string): Promise<Conversation> {
    return request<Conversation>(
      `/api/v1/chat/conversations/${conversationId}`
    );
  },

  async getMessages(
    conversationId: string,
    limit: number = 100
  ): Promise<Message[]> {
    return request<Message[]>(
      `/api/v1/chat/conversations/${conversationId}/messages?limit=${limit}`
    );
  },

  async sendMessage(
    conversationId: string,
    data: SendMessageRequest
  ): Promise<SendMessageResponse> {
    return request<SendMessageResponse>(
      `/api/v1/chat/conversations/${conversationId}/messages`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  // Admin endpoints
  async listConversations(params?: {
    agent_id?: string;
    status?: string;
    limit?: number;
  }): Promise<Conversation[]> {
    const queryParams = new URLSearchParams();
    if (params?.agent_id) queryParams.append("agent_id", params.agent_id);
    if (params?.status) queryParams.append("status", params.status);
    if (params?.limit) queryParams.append("limit", params.limit.toString());

    return request<Conversation[]>(
      `/api/v1/admin/conversations?${queryParams.toString()}`,
      {},
      true // require auth
    );
  },

  async handoffConversation(
    conversationId: string,
    adminId: string,
    reason?: string
  ): Promise<{ conversation_id: string; status: string; message: string }> {
    return request<{ conversation_id: string; status: string; message: string }>(
      `/api/v1/admin/conversations/${conversationId}/handoff`,
      {
        method: "POST",
        body: JSON.stringify({ admin_id: adminId, reason }),
      },
      true // require auth
    );
  },

  async returnToAI(
    conversationId: string,
    adminId: string
  ): Promise<{ conversation_id: string; status: string; message: string }> {
    return request(
      `/api/v1/admin/conversations/${conversationId}/return`,
      {
        method: "POST",
        body: JSON.stringify({ admin_id: adminId }),
      },
      true // require auth
    ) as Promise<{ conversation_id: string; status: string; message: string }>;
  },

  async getAuditLogs(params?: {
    admin_id?: string;
    resource_type?: string;
    limit?: number;
  }): Promise<any[]> {
    const queryParams = new URLSearchParams();
    if (params?.admin_id) queryParams.append("admin_id", params.admin_id);
    if (params?.resource_type)
      queryParams.append("resource_type", params.resource_type);
    if (params?.limit)
      queryParams.append("limit", params.limit.toString());

    return request<any[]>(
      `/api/v1/admin/audit?${queryParams.toString()}`,
      {},
      true // require auth
    );
  },

  async getStats(): Promise<{
    total_conversations: number;
    ai_active: number;
    needs_human: number;
    human_active: number;
    closed: number;
  }> {
    return request("/api/v1/admin/stats", {}, true); // require auth
  },
};

export { ApiError };

