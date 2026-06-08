export type RiskCategory = 'green' | 'yellow' | 'orange' | 'red'

export const RISK_LABELS: Record<RiskCategory, string> = {
  green: 'Low Risk',
  yellow: 'Moderate Risk',
  orange: 'Elevated Risk',
  red: 'Critical Risk',
}

export const RISK_DESCRIPTIONS: Record<RiskCategory, string> = {
  green: 'Sepsis risk is low. Continue standard monitoring.',
  yellow: 'Some warning signs detected. Increase observation frequency.',
  orange: 'Significant risk factors present. Consider early intervention.',
  red: 'High probability of sepsis. Immediate clinical review recommended.',
}

export const RISK_COLORS: Record<RiskCategory, string> = {
  green: '#10b981',
  yellow: '#f59e0b',
  orange: '#f97316',
  red: '#ef4444',
}

export function riskFromScore(score: number): RiskCategory {
  if (score < 0.15) return 'green'
  if (score < 0.35) return 'yellow'
  if (score < 0.6) return 'orange'
  return 'red'
}

export function isHighRisk(score: number): boolean {
  return score >= 0.6
}

export function predictionLabelFriendly(label: string): string {
  return label === 'sepsis_alert' ? 'Sepsis Alert' : 'No Alert'
}
