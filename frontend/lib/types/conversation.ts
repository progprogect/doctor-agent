/** Types for conversations. */

export type ConversationStatus =
  | "AI_ACTIVE"
  | "NEEDS_HUMAN"
  | "HUMAN_ACTIVE"
  | "CLOSED";

export interface Conversation {
  conversation_id: string;
  agent_id: string;
  status: ConversationStatus;
  created_at: string;
  updated_at: string;
  closed_at?: string;
  handoff_reason?: string;
  request_type?: string;
  ttl?: number;
}

export interface CreateConversationRequest {
  agent_id: string;
}

export interface CreateConversationResponse {
  conversation_id: string;
  agent_id: string;
  status: string;
}






