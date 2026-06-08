import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './endpoints'
import type { ExplainRequest, PredictRequest } from './types'

export const queryKeys = {
  health: ['health'] as const,
  systemStatus: ['systemStatus'] as const,
  modelVersion: ['modelVersion'] as const,
  metrics: ['metrics'] as const,
  history: (params?: object) => ['history', params] as const,
  audit: (params?: object) => ['audit', params] as const,
}

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.health,
    staleTime: 30_000,
  })
}

export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: api.systemStatus,
    refetchInterval: 15_000,
  })
}

export function useModelVersion() {
  return useQuery({
    queryKey: queryKeys.modelVersion,
    queryFn: api.modelVersion,
    staleTime: 60_000,
  })
}

export function useMetrics() {
  return useQuery({
    queryKey: queryKeys.metrics,
    queryFn: api.metrics,
    refetchInterval: 10_000,
  })
}

export function usePredictionHistory(params?: {
  date?: string
  limit?: number
  patient_id?: string
}) {
  return useQuery({
    queryKey: queryKeys.history(params),
    queryFn: () => api.predictionHistory(params),
    refetchInterval: 20_000,
  })
}

export function useAuditLogs(params?: {
  date?: string
  limit?: number
  prediction_label?: string
}) {
  return useQuery({
    queryKey: queryKeys.audit(params),
    queryFn: () => api.auditLogs(params),
    refetchInterval: 30_000,
  })
}

export function usePredict() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: PredictRequest) => api.predict(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['history'] })
      qc.invalidateQueries({ queryKey: ['audit'] })
      qc.invalidateQueries({ queryKey: queryKeys.metrics })
      qc.invalidateQueries({ queryKey: queryKeys.systemStatus })
    },
  })
}

export function useExplain() {
  return useMutation({
    mutationFn: (body: ExplainRequest) => api.explain(body),
  })
}

export function useAnalyticsExecutive() {
  return useQuery({
    queryKey: ['analytics', 'executive'],
    queryFn: api.analyticsExecutive,
    refetchInterval: 15_000,
  })
}

export function useAnalyticsPopulation() {
  return useQuery({
    queryKey: ['analytics', 'population'],
    queryFn: api.analyticsPopulation,
    refetchInterval: 30_000,
  })
}

export function useAnalyticsCapacity() {
  return useQuery({
    queryKey: ['analytics', 'capacity'],
    queryFn: api.analyticsCapacity,
    refetchInterval: 20_000,
  })
}

export function useAnalyticsResources() {
  return useQuery({
    queryKey: ['analytics', 'resources'],
    queryFn: api.analyticsResources,
    refetchInterval: 25_000,
  })
}

export function useAnalyticsKPIs() {
  return useQuery({
    queryKey: ['analytics', 'kpis'],
    queryFn: api.analyticsKPIs,
    refetchInterval: 15_000,
  })
}

export function useAnalyticsCompareModels() {
  return useQuery({
    queryKey: ['analytics', 'compareModels'],
    queryFn: api.analyticsCompareModels,
    staleTime: 60_000,
  })
}
