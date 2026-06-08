import { lazy, Suspense } from 'react'

import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'

import { LandingPage } from '@/pages/LandingPage'

import { CommandCenterPage } from '@/pages/CommandCenterPage'

import { LiveMonitoringPage } from '@/pages/LiveMonitoringPage'

import { PatientRiskPage } from '@/pages/PatientRiskPage'

import { ShapExplainPage } from '@/pages/ShapExplainPage'

import { PredictionHistoryPage } from '@/pages/PredictionHistoryPage'

import { AuditLogPage } from '@/pages/AuditLogPage'

import { ModelPerformancePage } from '@/pages/ModelPerformancePage'

import { SystemHealthPage } from '@/pages/SystemHealthPage'

import { SettingsPage } from '@/pages/SettingsPage'
import { CopilotPage } from '@/pages/CopilotPage'
import { CopilotPatientPage } from '@/pages/CopilotPatientPage'
import { CopilotExecutivePage } from '@/pages/CopilotExecutivePage'
import { AnalyticsDashboardPage } from '@/pages/AnalyticsDashboardPage'
import { TenantManagementPage } from '@/pages/TenantManagementPage'
import { LoginPage } from '@/pages/LoginPage'

import { Spinner } from '@/components/ui/Spinner'

import { ROUTES } from './paths'



const DigitalTwinPage = lazy(() =>

  import('@/three/pages/DigitalTwinPage').then((m) => ({ default: m.DigitalTwinPage })),

)

const Executive3DPage = lazy(() =>

  import('@/three/pages/Executive3DPage').then((m) => ({ default: m.Executive3DPage })),

)

const Patient3DPage = lazy(() =>

  import('@/three/pages/Patient3DPage').then((m) => ({ default: m.Patient3DPage })),

)



function SceneLoader() {

  return (

    <div className="flex h-screen items-center justify-center bg-slate-950">

      <Spinner size="lg" label="Loading 3D Command Center..." />

    </div>

  )

}



function LazyScene({ children }: { children: React.ReactNode }) {

  return <Suspense fallback={<SceneLoader />}>{children}</Suspense>

}



import { AuthGuard } from '@/components/auth/AuthGuard'

export const router = createBrowserRouter([

  {

    path: '/',

    element: (
      <AuthGuard>
        <AppShell />
      </AuthGuard>
    ),

    children: [

      { index: true, element: <LandingPage /> },

      { path: ROUTES.commandCenter.slice(1), element: <CommandCenterPage /> },

      { path: ROUTES.liveMonitoring.slice(1), element: <LiveMonitoringPage /> },

      { path: ROUTES.patientRisk.slice(1), element: <PatientRiskPage /> },

      { path: ROUTES.shapExplain.slice(1), element: <ShapExplainPage /> },

      { path: ROUTES.predictionHistory.slice(1), element: <PredictionHistoryPage /> },

      { path: ROUTES.auditLogs.slice(1), element: <AuditLogPage /> },

      { path: ROUTES.modelPerformance.slice(1), element: <ModelPerformancePage /> },

      { path: ROUTES.systemHealth.slice(1), element: <SystemHealthPage /> },

      { path: ROUTES.settings.slice(1), element: <SettingsPage /> },
      { path: ROUTES.copilot.slice(1), element: <CopilotPage /> },
      { path: ROUTES.copilotPatient.slice(1), element: <CopilotPatientPage /> },
      { path: ROUTES.copilotExecutive.slice(1), element: <CopilotExecutivePage /> },
      { path: ROUTES.analyticsDashboard.slice(1), element: <AnalyticsDashboardPage /> },
      { path: ROUTES.tenantManagement.slice(1), element: <TenantManagementPage /> },

      { path: '*', element: <Navigate to={ROUTES.landing} replace /> },

    ],

  },

  {
    // Standalone login page — no AppShell (no nav/sidebar)
    path: ROUTES.login,
    element: <LoginPage />,
  },

  {

    path: ROUTES.digitalTwin,

    element: (
      <AuthGuard>
        <LazyScene>
          <DigitalTwinPage />
        </LazyScene>
      </AuthGuard>
    ),

  },

  {

    path: ROUTES.executive3d,

    element: (
      <AuthGuard>
        <LazyScene>
          <Executive3DPage />
        </LazyScene>
      </AuthGuard>
    ),

  },

  {

    path: `${ROUTES.patient3d}/:id`,

    element: (
      <AuthGuard>
        <LazyScene>
          <Patient3DPage />
        </LazyScene>
      </AuthGuard>
    ),

  },

])


