export interface ApiModelOption {
  id: string;
  label: string;
  provider_value: string;
}

export interface ApiConfig {
  models: ApiModelOption[];
  search_methods: string[];
  default_model_id: string;
  default_search_method: string;
}

export interface ApiSessionSummary {
  id: string;
  title: string;
  preview: string;
  last_active: string;
}

export interface ApiChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Record<string, string>;
  suggestions?: string[];
  ragas_eval?: {
    faithfulness: number;
    answer_relevancy: number;
  }
  thoughtDurationSeconds?: number;
}

export interface ApiSessionDetail {
  session_id: string;
  messages: ApiChatMessage[];
}

export interface ApiChatCompletionResponse {
  session_id: string;
  status: string;
  user_message: ApiChatMessage;
  assistant_message: ApiChatMessage;
}

export interface ApiErrorBody {
  detail: string;
  code?: string;
}

export interface SourceLink {
  id: number;
  label: string;
  url: string;
}

export interface ChatHistoryItem {
  id: string;
  title: string;
  lastActive: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Record<string, string>;
  suggestions?: string[];
  ragas_eval?: {
    faithfulness: number;
    answer_relevancy: number;
  };
  thoughtDurationSeconds?: number;
}

export function sourcesToLinks(sources: Record<string, string> = {}): SourceLink[] {
  return Object.entries(sources)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([id, url]) => ({
      id: Number(id),
      label: url,
      url,
    }));
}
