/** Statistics types. */

export interface Stats {
  total_conversations: number;
  ai_active: number;
  needs_human: number;
  human_active: number;
  closed: number;
  marketing_new: number;
  marketing_booked: number;
  marketing_no_response: number;
  marketing_rejected: number;
  period: string;
  comparison?: StatsComparison;
}

export interface StatsComparison {
  total_conversations: number;
  ai_active: number;
  needs_human: number;
  human_active: number;
  closed: number;
  marketing_new: number;
  marketing_booked: number;
  marketing_no_response: number;
  marketing_rejected: number;
}

export type Period = "today" | "last_7_days" | "last_30_days";
