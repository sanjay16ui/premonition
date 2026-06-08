import { describe, it, expect } from 'vitest'
import { formatPercent, formatUptime } from '@/utils/format'
import { riskFromScore, isHighRisk, RISK_LABELS } from '@/utils/risk'

describe('format utils', () => {
  it('formats percent', () => {
    expect(formatPercent(0.956)).toBe('95.6%')
  })

  it('formats uptime', () => {
    expect(formatUptime(3661)).toBe('1h 1m')
    expect(formatUptime(90)).toBe('1m 30s')
  })
})

describe('risk utils', () => {
  it('maps score to category', () => {
    expect(riskFromScore(0.05)).toBe('green')
    expect(riskFromScore(0.25)).toBe('yellow')
    expect(riskFromScore(0.45)).toBe('orange')
    expect(riskFromScore(0.85)).toBe('red')
  })

  it('detects high risk', () => {
    expect(isHighRisk(0.7)).toBe(true)
    expect(isHighRisk(0.3)).toBe(false)
  })

  it('has labels for all categories', () => {
    expect(RISK_LABELS.green).toBe('Low Risk')
    expect(RISK_LABELS.red).toBe('Critical Risk')
  })
})
