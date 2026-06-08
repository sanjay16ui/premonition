import type { AlertLevel, PatientMonitorState } from '@/api/types'

export const RISK_COLORS: Record<AlertLevel, string> = {
  GREEN: '#10b981',
  YELLOW: '#f59e0b',
  ORANGE: '#f97316',
  RED: '#ef4444',
  BLACK: '#1e1b4b',
}

export const RISK_EMISSIVE: Record<AlertLevel, string> = {
  GREEN: '#064e3b',
  YELLOW: '#78350f',
  ORANGE: '#7c2d12',
  RED: '#7f1d1d',
  BLACK: '#312e81',
}

export function alertLevelFromPatient(p: PatientMonitorState): AlertLevel {
  if (p.alert_level) return p.alert_level
  if (p.risk_score >= 0.85) return 'BLACK'
  if (p.risk_score >= 0.6) return 'RED'
  if (p.risk_score >= 0.35) return 'ORANGE'
  if (p.risk_score >= 0.15) return 'YELLOW'
  return 'GREEN'
}

export function riskColor(patient: PatientMonitorState): string {
  return RISK_COLORS[alertLevelFromPatient(patient)]
}

export function riskEmissive(patient: PatientMonitorState): string {
  return RISK_EMISSIVE[alertLevelFromPatient(patient)]
}

export function isCritical(patient: PatientMonitorState): boolean {
  const level = alertLevelFromPatient(patient)
  return level === 'RED' || level === 'BLACK'
}
