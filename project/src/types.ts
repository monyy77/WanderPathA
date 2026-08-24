export type AgentId = "memory" | "planning" | "flight" | "refund" | "vip";

export type StepState = "pending" | "running" | "done" | "error";

export interface Step {
  label: string;
  state: StepState;
}

export type AgentStatus = "idle" | "thinking" | "completed" | "error";

export interface Agent {
  id: AgentId;
  name: string;
  tagline: string;
  description: string;
  icon: string;
  accent: "indigo" | "violet" | "sky" | "rose" | "amber";
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  sessionId: string;
  agentId: AgentId;
  role: MessageRole;
  content: string;
  steps?: Step[];
  status?: "completed" | "error";
  createdAt: string;
}

export interface ChatRequest {
  agent_id: AgentId;
  session_id: string;
  message: string;
}

export interface ChatResponse {
  session_id: string;
  agent_id: AgentId;
  message_id: string;
  role: "assistant";
  content: string;
  status: "completed" | "error";
  steps: Step[];
  created_at: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
}
