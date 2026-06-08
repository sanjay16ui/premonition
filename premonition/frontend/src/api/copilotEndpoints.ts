import { apiClient } from './client'
import type {
  ChatRequest,
  ConversationDetail,
  ConversationSummary,
  CopilotResponse,
  SearchResponse,
} from './copilotTypes'

export const copilotApi = {
  chat: (body: ChatRequest) =>
    apiClient.post<CopilotResponse>('/copilot/chat', body).then((r) => r.data),

  explainPrediction: (body: Record<string, unknown>) =>
    apiClient.post<CopilotResponse>('/copilot/explain-prediction', body).then((r) => r.data),

  explainAlert: (body: Record<string, unknown>) =>
    apiClient.post<CopilotResponse>('/copilot/explain-alert', body).then((r) => r.data),

  generateSummary: async (patientId: string): Promise<CopilotResponse> => {
    const res = await apiClient.post<CopilotResponse>(`/copilot/patient-summary`, { patient_id: patientId })
    return res.data
  },

  handover: (body: { patient_ids: string[] }) =>
    apiClient.post<CopilotResponse>('/copilot/handover', body).then((r) => r.data),

  executiveSummary: (body?: Record<string, unknown>) =>
    apiClient.post<CopilotResponse>('/copilot/executive-summary', body ?? {}).then((r) => r.data),

  recommendations: (body: Record<string, unknown>) =>
    apiClient.post<CopilotResponse>('/copilot/recommendations', body).then((r) => r.data),

  ingestDocument: (body: { title: string; content: string; doc_type?: string }) =>
    apiClient.post<{ document_id: string; chunks: number }>('/copilot/ingest-document', body).then((r) => r.data),

  search: (body: { query: string; top_k?: number }) =>
    apiClient.post<SearchResponse>('/copilot/search', body).then((r) => r.data),

  conversations: () =>
    apiClient.get<ConversationSummary[]>('/copilot/conversations').then((r) => r.data),

  conversation: (id: string) =>
    apiClient.get<ConversationDetail>(`/copilot/conversations/${id}`).then((r) => r.data),
}
