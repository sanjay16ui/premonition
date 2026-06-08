import { apiClient } from './client'
import type {
  AuditLogResponse,
  ExplainRequest,
  ExplainResponse,
  HealthResponse,
  MetricsResponse,
  ModelVersionResponse,
  PredictRequest,
  PredictResponse,
  PredictionHistoryResponse,
  SystemStatusResponse,
} from './types'

export const api = {
  health: () =>
    apiClient.get<HealthResponse>('/health').then((r) => r.data),

  systemStatus: () =>
    apiClient.get<SystemStatusResponse>('/system/status').then((r) => r.data),

  modelVersion: () =>
    apiClient.get<ModelVersionResponse>('/models/version').then((r) => r.data),

  predict: (body: PredictRequest) =>
    apiClient.post<PredictResponse>('/predict', body).then((r) => r.data),

  explain: (body: ExplainRequest) =>
    apiClient.post<ExplainResponse>('/explain', body).then((r) => r.data),

  predictionHistory: (params?: {
    date?: string
    limit?: number
    patient_id?: string
  }) =>
    apiClient
      .get<PredictionHistoryResponse>('/predictions/history', { params })
      .then((r) => r.data),

  auditLogs: (params?: {
    date?: string
    limit?: number
    prediction_label?: string
  }) =>
    apiClient
      .get<AuditLogResponse>('/audit/logs', { params })
      .then((r) => r.data),

  metrics: () =>
    apiClient.get<MetricsResponse>('/metrics').then((r) => r.data),

  analyticsExecutive: () =>
    apiClient.get<any>('/analytics/executive').then((r) => r.data),

  analyticsPopulation: () =>
    apiClient.get<any>('/analytics/population').then((r) => r.data),

  analyticsCapacity: () =>
    apiClient.get<any>('/analytics/capacity').then((r) => r.data),

  analyticsResources: () =>
    apiClient.get<any>('/analytics/resources').then((r) => r.data),

  analyticsKPIs: () =>
    apiClient.get<any>('/analytics/kpis').then((r) => r.data),

  analyticsCompareModels: () =>
    apiClient.post<any>('/analytics/compare-models').then((r) => r.data),
}
