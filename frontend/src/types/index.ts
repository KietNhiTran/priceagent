/* ------------------------------------------------------------------ */
/*  Shared TypeScript types for the LLPG Price Beat Agent frontend    */
/* ------------------------------------------------------------------ */

// ---- Enums --------------------------------------------------------

export type Decision = "AUTO_APPROVE" | "SEND_TO_REVIEW" | "AUTO_REJECT" | "NOT_LLPG" | "INCOMPLETE" | "NO_MATCH";

export type StepStatus = "pending" | "running" | "completed" | "failed";

export type InferenceMode = "real" | "fallback";

// ---- Agent Step ---------------------------------------------------

export interface AgentStep {
  step_id: string;
  agent_name: string;
  status: StepStatus;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  inference_mode?: InferenceMode;
  input_summary?: string;
  output_summary?: string;
  raw_json?: Record<string, unknown>;
}

// ---- Trace --------------------------------------------------------

export interface TraceDecision {
  decision: Decision;
  reason_code: string;
  beat_price?: number;
  rsa_compliant?: boolean;
  competitor_name?: string;
  competitor_price?: number;
  our_product_name?: string;
  our_sku?: string;
}

export interface AgentTrace {
  trace_id: string;
  session_id: string;
  timestamp: string;
  total_duration_ms: number;
  final_decision: Decision;
  user_message: string;
  steps: AgentStep[];
  decision: TraceDecision;
}

// ---- WebSocket Messages -------------------------------------------

export interface WsAgentStepMessage {
  type: "agent_step";
  step: AgentStep;
}

export interface WsChatMessage {
  type: "chat_message";
  message: string;
  decision?: Decision;
  beat_price?: number;
  trace_id?: string;
}

export interface WsTraceCompleteMessage {
  type: "trace_complete";
  trace: AgentTrace;
}

export interface WsWelcomeMessage {
  type: "welcome";
  message: string;
}

export interface WsErrorMessage {
  type: "error";
  message: string;
}

export type WsMessage =
  | WsAgentStepMessage
  | WsChatMessage
  | WsTraceCompleteMessage
  | WsWelcomeMessage
  | WsErrorMessage;

// ---- Chat ---------------------------------------------------------

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  decision?: Decision;
  beat_price?: number;
  trace_id?: string;
  imageUrl?: string;
}

// ---- Product Comparison -------------------------------------------

export interface ProductComparison {
  our_product: string;
  our_sku: string;
  our_price: number;
  competitor_name: string;
  competitor_product: string;
  competitor_price: number;
  beat_price?: number;
  rsa_floor?: number;
  rsa_compliant?: boolean;
  decision: Decision;
}

// ---- Agent pipeline definition ------------------------------------

export const AGENT_PIPELINE: { name: string; label: string }[] = [
  { name: "IntentAgent", label: "Intent" },
  { name: "URLValidationAgent", label: "URL Check" },
  { name: "ScrapingAgent", label: "Scrape" },
  { name: "ProductMatchingAgent", label: "Match" },
  { name: "LLPGRuleAgent", label: "Rules" },
  { name: "DecisionAgent", label: "Decision" },
];
