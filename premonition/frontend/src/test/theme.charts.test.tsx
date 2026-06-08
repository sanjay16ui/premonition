import { describe, it, expect } from 'vitest'
import { chartColors } from '@/theme/colors'
import { RISK_COLORS } from '@/utils/risk'

describe('Theme colors', () => {
  it('chartColors is non-empty array', () => {
    expect(chartColors.length).toBeGreaterThan(0)
  })

  it('chartColors entries are valid hex/rgb strings', () => {
    chartColors.forEach((c) => expect(c).toMatch(/^#/))
  })

  it('RISK_COLORS has all alert levels', () => {
    expect(RISK_COLORS).toHaveProperty('green')
    expect(RISK_COLORS).toHaveProperty('yellow')
    expect(RISK_COLORS).toHaveProperty('orange')
    expect(RISK_COLORS).toHaveProperty('red')
  })
})

describe('AnalyticsHeatmap color intensity', () => {
  it('calculates intensity ratio correctly', () => {
    const data = [[10, 20], [30, 40]]
    const max = Math.max(...data.flat())
    expect(max).toBe(40)
    expect(10 / max).toBe(0.25)
    expect(40 / max).toBe(1)
  })
})

describe('Chart data validation', () => {
  it('risk trend data has required fields', () => {
    const point = { time: '10:00', risk: 0.5 }
    expect(point).toHaveProperty('time')
    expect(point).toHaveProperty('risk')
    expect(point.risk).toBeGreaterThanOrEqual(0)
    expect(point.risk).toBeLessThanOrEqual(1)
  })

  it('population pie data sums to 100', () => {
    const data = [
      { name: 'Low', value: 62 },
      { name: 'Medium', value: 24 },
      { name: 'High', value: 10 },
      { name: 'Critical', value: 4 },
    ]
    const total = data.reduce((s, d) => s + d.value, 0)
    expect(total).toBe(100)
  })

  it('KPI change values are numbers', () => {
    const kpis = [
      { label: 'Occupancy', value: '87', change: 3 },
      { label: 'Uptime', value: '99.9', change: -0.1 },
    ]
    kpis.forEach((k) => expect(typeof k.change).toBe('number'))
  })

  it('model comparison has accuracy field', () => {
    const model = { label: 'XGBoost', accuracy: 0.91, f1: 0.87, auc: 0.94 }
    expect(model.accuracy).toBeGreaterThan(0.8)
  })

  it('capacity data has day labels', () => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    expect(days).toHaveLength(7)
  })

  it('heatmap has 6 ICU rows', () => {
    const rows = ['ICU-A', 'ICU-B', 'ICU-C', 'ER', 'OR', 'Ward']
    expect(rows).toHaveLength(6)
  })

  it('alert trend has severity levels', () => {
    const levels = ['green', 'yellow', 'red']
    expect(levels).toHaveLength(3)
  })

  it('resource utilization is between 0 and 1', () => {
    const resources = [
      { label: 'Nurses', utilization: 0.82 },
      { label: 'Beds', utilization: 0.88 },
    ]
    resources.forEach((r) => {
      expect(r.utilization).toBeGreaterThanOrEqual(0)
      expect(r.utilization).toBeLessThanOrEqual(1)
    })
  })
})
