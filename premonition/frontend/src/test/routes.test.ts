import { describe, it, expect } from 'vitest'
import { ROUTES } from '@/routes/paths'

describe('ROUTES', () => {
  it('defines landing route', () => {
    expect(ROUTES.landing).toBe('/')
  })

  it('defines command center route', () => {
    expect(ROUTES.commandCenter).toBe('/command-center')
  })

  it('defines monitoring route', () => {
    expect(ROUTES.liveMonitoring).toBe('/monitoring')
  })

  it('defines copilot routes', () => {
    expect(ROUTES.copilot).toBe('/copilot')
    expect(ROUTES.copilotPatient).toBe('/copilot/patient')
    expect(ROUTES.copilotExecutive).toBe('/copilot/executive')
  })

  it('defines analytics dashboard route', () => {
    expect(ROUTES.analyticsDashboard).toBe('/analytics')
  })

  it('defines tenant management route', () => {
    expect(ROUTES.tenantManagement).toBe('/tenants')
  })

  it('defines 3D routes', () => {
    expect(ROUTES.digitalTwin).toBe('/digital-twin')
    expect(ROUTES.executive3d).toBe('/executive-3d')
    expect(ROUTES.patient3d).toBe('/patient-3d')
  })
})
