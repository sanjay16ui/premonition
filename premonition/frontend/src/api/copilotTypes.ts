export interface CopilotCitation {
  source_id: string
  title: string
  excerpt: string
  score: number
  chunk_index: number
}

export interface CopilotResponse {
  conversation_id: string
  message: string
  citations: CopilotCitation[]
  prompt_version: string
  model: string
  retrieval_trace: string[]
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  patient_id?: string
}

export interface ConversationSummary {
  id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface ConversationDetail {
  id: string
  title: string
  messages: { role: string; content: string }[]
  created_at: string
  updated_at: string
}

export interface SearchResponse {
  query: string
  context: string
  citations: CopilotCitation[]
  retrieval_trace: string[]
}
