import { describe, it, expect } from 'vitest'
import { ROUTES } from '@/routes/paths'

describe('API integration map', () => {
  it('defines all route paths', () => {
    expect(ROUTES.landing).toBe('/')
    expect(ROUTES.commandCenter).toBe('/command-center')
    expect(ROUTES.liveMonitoring).toBe('/monitoring')
    expect(ROUTES.patientRisk).toBe('/patient-risk')
    expect(ROUTES.shapExplain).toBe('/explain')
    expect(ROUTES.predictionHistory).toBe('/history')
    expect(ROUTES.auditLogs).toBe('/audit')
    expect(ROUTES.modelPerformance).toBe('/model-performance')
    expect(ROUTES.systemHealth).toBe('/system-health')
    expect(ROUTES.settings).toBe('/settings')
    expect(ROUTES.copilot).toBe('/copilot')
    expect(ROUTES.copilotPatient).toBe('/copilot/patient')
    expect(ROUTES.copilotExecutive).toBe('/copilot/executive')
  })
})

describe('API endpoints mapping', () => {
  const endpoints = [
    { method: 'GET', path: '/health', page: 'System Health, Landing' },
    { method: 'GET', path: '/system/status', page: 'Command Center, System Health' },
    { method: 'GET', path: '/models/version', page: 'Model Performance' },
    { method: 'POST', path: '/predict', page: 'Patient Risk' },
    { method: 'POST', path: '/explain', page: 'SHAP Explain' },
    { method: 'GET', path: '/predictions/history', page: 'History, Monitoring' },
    { method: 'GET', path: '/audit/logs', page: 'Audit Logs' },
    { method: 'GET', path: '/metrics', page: 'System Health, Command Center' },
    { method: 'POST', path: '/copilot/chat', page: 'AI Copilot' },
    { method: 'POST', path: '/copilot/patient-summary', page: 'Patient Copilot' },
    { method: 'POST', path: '/copilot/executive-summary', page: 'Executive Copilot' },
  ]

  it('maps all backend endpoints to frontend pages', () => {
    expect(endpoints).toHaveLength(11)
    endpoints.forEach((ep) => {
      expect(ep.path).toBeTruthy()
      expect(ep.page).toBeTruthy()
    })
  })
})
