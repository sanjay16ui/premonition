export const ROUTES = {
  landing: '/',
  login: '/login',
  commandCenter: '/command-center',
  liveMonitoring: '/monitoring',
  patientRisk: '/patient-risk',
  shapExplain: '/explain',
  predictionHistory: '/history',
  auditLogs: '/audit',
  modelPerformance: '/model-performance',
  systemHealth: '/system-health',
  settings: '/settings',
  digitalTwin: '/digital-twin',
  executive3d: '/executive-3d',
  patient3d: '/patient-3d',
  copilot: '/copilot',
  copilotPatient: '/copilot/patient',
  copilotExecutive: '/copilot/executive',
  analyticsDashboard: '/analytics',
  tenantManagement: '/tenants',
} as const

export type RoutePath = (typeof ROUTES)[keyof typeof ROUTES]
