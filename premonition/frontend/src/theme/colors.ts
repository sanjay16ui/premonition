/** PREMONITION healthcare AI color palette */

export const palette = {
  primary: '#0ea5e9',      // sky-500 — trust, clinical
  secondary: '#8b5cf6',    // violet-500 — AI intelligence
  accent: '#06b6d4',       // cyan-500 — data flow
  success: '#10b981',      // emerald-500
  warning: '#f59e0b',      // amber-500
  danger: '#ef4444',       // red-500
  info: '#3b82f6',         // blue-500

  // Risk tiers
  riskGreen: '#10b981',
  riskYellow: '#f59e0b',
  riskOrange: '#f97316',
  riskRed: '#ef4444',

  // Gradients
  gradientHero: 'linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 50%, #06b6d4 100%)',
  gradientCard: 'linear-gradient(135deg, rgba(14,165,233,0.1) 0%, rgba(139,92,246,0.1) 100%)',
} as const

export const chartColors = [
  '#0ea5e9',
  '#8b5cf6',
  '#06b6d4',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#ec4899',
  '#6366f1',
]

/* ─── Traffic Light System ──────────────────────────────────── */

export const trafficLight = {
  GREEN:  { bg: '#10b981', text: '#fff', glow: 'rgba(16,185,129,0.5)', label: 'SAFE',        emoji: '🟢' },
  YELLOW: { bg: '#f59e0b', text: '#000', glow: 'rgba(245,158,11,0.5)', label: 'WATCH',       emoji: '🟡' },
  ORANGE: { bg: '#f97316', text: '#fff', glow: 'rgba(249,115,22,0.5)', label: 'HIGH RISK',   emoji: '🟠' },
  RED:    { bg: '#ef4444', text: '#fff', glow: 'rgba(239,68,68,0.5)',  label: 'CRITICAL',    emoji: '🔴' },
  BLACK:  { bg: '#1e1b4b', text: '#fff', glow: 'rgba(30,27,75,0.7)',   label: 'EMERGENCY',   emoji: '⚫' },
} as const

export type AlertLevel = keyof typeof trafficLight

/** Map a 0-1 risk score to a traffic light level */
export function riskToLevel(score: number): AlertLevel {
  if (score >= 0.9) return 'BLACK'
  if (score >= 0.7) return 'RED'
  if (score >= 0.5) return 'ORANGE'
  if (score >= 0.3) return 'YELLOW'
  return 'GREEN'
}

/** Human-readable risk label for non-technical users */
export function humanRiskLabel(score: number): { title: string; subtitle: string; level: AlertLevel } {
  const level = riskToLevel(score)
  const pct = `${Math.round(score * 100)}% probability`
  switch (level) {
    case 'BLACK':  return { title: 'EMERGENCY PATIENT', subtitle: pct + ' — Immediate intervention required', level }
    case 'RED':    return { title: 'CRITICAL PATIENT',  subtitle: pct + ' — Immediate attention recommended', level }
    case 'ORANGE': return { title: 'HIGH RISK PATIENT', subtitle: pct + ' — Close monitoring required',       level }
    case 'YELLOW': return { title: 'WATCH PATIENT',     subtitle: pct + ' — Continue monitoring',              level }
    case 'GREEN':  return { title: 'STABLE PATIENT',    subtitle: pct + ' — No immediate concerns',           level }
  }
}

/* ─── Glassmorphism tokens ──────────────────────────────────── */

export const glass = {
  background: 'rgba(15, 23, 42, 0.6)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  backdropFilter: 'blur(16px) saturate(180%)',
  shadow: '0 8px 32px rgba(0, 0, 0, 0.25)',
} as const

