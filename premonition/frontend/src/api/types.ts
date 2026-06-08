/** TypeScript types mirroring FastAPI response schemas */

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export interface SystemStatusResponse {
  status: string
  model_loaded: boolean
  model_name: string | null
  model_version: string | null
  tier: string
  uptime_seconds: number
  predictions_served: number
  last_prediction_at: string | null
}

export interface ModelVersionResponse {
  model_name: string
  model_version: string
  tier: string
  training_timestamp: string | null
  dataset_hash: string | null
  n_features: number
  feature_set: string[]
  metrics: Record<string, unknown>
}

export interface ContributingFactor {
  rank: number
  feature: string
  contribution_pct: number
  direction: string
  shap_value: number | null
  category: string | null
}

export interface ShapExplanation {
  base_value: number
  top_factors: ContributingFactor[]
  risk_increasers: string[]
  risk_decreasers: string[]
  dominant_category: string | null
}

export interface PredictResponse {
  patient_id: string
  risk_score: number
  risk_pct: string
  prediction: number
  prediction_label: string
  confidence: string
  risk_category: string
  model_name: string
  model_version: string
  explanation_summary: string | null
  top_factors: ContributingFactor[]
  shap: ShapExplanation | null
  request_id: string | null
  timestamp: string
}

export interface BatchPredictResponse {
  count: number
  predictions: PredictResponse[]
  request_id: string | null
}

export interface ExplainResponse {
  patient_id: string
  risk_score: number
  risk_pct: string
  confidence: string
  risk_category: string
  explanation_summary: string
  top_factors: ContributingFactor[]
  shap: ShapExplanation
  request_id: string | null
}

export interface PredictionHistoryItem {
  timestamp: string
  patient_id: string
  risk_score: number
  prediction_label: string
  confidence: string
  model_name: string
  explanation_summary: string | null
}

export interface PredictionHistoryResponse {
  date: string
  count: number
  items: PredictionHistoryItem[]
}

export interface AuditLogItem {
  timestamp: string
  patient_id: string
  risk_score: number
  prediction_label: string
  confidence: string
  model_name: string
  model_version: string
  explanation_summary: string
  top_factors: string[]
  request_id: string | null
}

export interface AuditLogResponse {
  date: string
  count: number
  items: AuditLogItem[]
}

export interface MetricsResponse {
  predictions_total: number
  predictions_sepsis_alerts: number
  predictions_errors: number
  model_loaded: number
  uptime_seconds: number
  avg_latency_ms: number
}

export interface PatientFeatures {
  subject_id?: number | string | null
  age: number
  gender: string
  weight_kg: number
  height_cm: number
  bmi: number | null
  ethnicity: string
  insurance: string
  diabetes: number
  hypertension: number
  chf: number
  copd: number
  chronic_kidney_disease: number
  liver_disease: number
  immunosuppression: number
  cad: number
  atrial_fibrillation: number
  cancer_active: number
  hospital_admit_source: string
  icu_admit_time_hour: number
  day_of_week: number
  hr_mean: number
  hr_max: number
  hr_min: number
  hr_std: number
  sbp_mean: number
  sbp_max: number
  sbp_min: number
  sbp_std: number
  dbp_mean: number
  dbp_max: number
  dbp_min: number
  dbp_std: number
  map_mean: number | null
  temp_celsius_mean: number
  temp_celsius_max: number
  temp_celsius_min: number
  temp_celsius_std: number
  spo2_mean: number
  spo2_min: number
  spo2_max: number
  spo2_std: number
  respiratory_rate_mean: number
  respiratory_rate_max: number
  respiratory_rate_min: number
  respiratory_rate_std: number
}

export interface PredictRequest {
  patient_id: number | string
  features: PatientFeatures
  include_shap?: boolean
  include_explanation?: boolean
}

export interface ExplainRequest {
  patient_id: number | string
  features: PatientFeatures
  top_n?: number
}

export interface ApiError {
  error: string
  message: string
  request_id?: string
  details?: { field: string; message: string; code: string }[]
}

export type AlertLevel = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED' | 'BLACK'

export interface VitalsSnapshot {
  hr_mean: number
  sbp_mean: number
  dbp_mean: number
  spo2_mean: number
  temp_celsius_mean: number
  respiratory_rate_mean: number
  shock_index?: number | null
}

export interface Recommendation {
  text: string
  reason: string
  priority: string
  related_factors?: string[]
}

export interface AlertRecord {
  timestamp: string
  patient_id: string
  alert_level: AlertLevel
  alert_type: string
  risk_score: number
  confidence: string
  reason: string
  recommendation?: string | null
}

export interface PatientMonitorState {
  patient_id: string
  risk_score: number
  risk_category: string
  alert_level: AlertLevel
  confidence: string
  prediction_label: string
  deterioration_rate: number
  alert_count: number
  active_alerts: AlertRecord[]
  recommendations: Recommendation[]
  vitals: VitalsSnapshot | null
  risk_history: number[]
  last_updated: string
  priority_score: number
  rank: number
}

export interface ExecutiveSummary {
  current_icu_patients: number
  high_risk_count: number
  critical_alert_count: number
  black_alert_count: number
  average_risk_score: number
  predictions_today: number
  alerts_today: number
  model_accuracy: number | null
  system_uptime_seconds: number
  top_critical: PatientMonitorState[]
  top_escalating: PatientMonitorState[]
  top_stable: PatientMonitorState[]
}

export interface PriorityRanking {
  critical: PatientMonitorState[]
  escalating: PatientMonitorState[]
  stable: PatientMonitorState[]
}
