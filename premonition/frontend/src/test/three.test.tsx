import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import {
  alertLevelFromPatient,
  riskColor,
  isCritical,
  RISK_COLORS,
} from '@/three/utils/riskColors'
import { useSceneStore } from '@/three/store/sceneStore'
import { PatientIntelligencePanel } from '@/three/components/ui/PatientIntelligencePanel'
import { ROUTES } from '@/routes/paths'
import type { PatientMonitorState } from '@/api/types'

vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="r3f-canvas">{children}</div>
  ),
  useFrame: vi.fn(),
  useThree: () => ({ camera: {}, scene: {} }),
}))

vi.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
  PerspectiveCamera: () => null,
  Stars: () => null,
  Text: ({ children }: { children: string }) => <span>{children}</span>,
}))

const mockPatient: PatientMonitorState = {
  patient_id: '37464',
  risk_score: 0.85,
  risk_category: 'red',
  alert_level: 'RED',
  confidence: 'High',
  prediction_label: 'sepsis_alert',
  deterioration_rate: 0.1,
  alert_count: 2,
  active_alerts: [
    {
      timestamp: '2026-06-05T12:00:00Z',
      patient_id: '37464',
      alert_level: 'RED',
      alert_type: 'Possible Sepsis',
      risk_score: 0.85,
      confidence: 'High',
      reason: 'High sepsis probability',
    },
  ],
  recommendations: [
    {
      text: 'Urgent clinician review recommended.',
      reason: 'High confidence sepsis risk',
      priority: 'high',
    },
  ],
  vitals: {
    hr_mean: 110,
    sbp_mean: 95,
    dbp_mean: 60,
    spo2_mean: 91,
    temp_celsius_mean: 38.5,
    respiratory_rate_mean: 26,
    shock_index: 1.16,
  },
  risk_history: [0.7, 0.85],
  last_updated: '2026-06-05T12:00:00Z',
  priority_score: 0.9,
  rank: 1,
}

describe('riskColors utils', () => {
  it('maps high risk to RED', () => {
    expect(alertLevelFromPatient(mockPatient)).toBe('RED')
    expect(riskColor(mockPatient)).toBe(RISK_COLORS.RED)
  })

  it('detects critical patients', () => {
    expect(isCritical(mockPatient)).toBe(true)
    expect(isCritical({ ...mockPatient, risk_score: 0.1, alert_level: 'GREEN' })).toBe(false)
  })

  it('maps black alert level', () => {
    const black = { ...mockPatient, alert_level: 'BLACK' as const, risk_score: 0.95 }
    expect(alertLevelFromPatient(black)).toBe('BLACK')
    expect(riskColor(black)).toBe(RISK_COLORS.BLACK)
  })

  it('maps yellow from risk score', () => {
    const yellow = { ...mockPatient, alert_level: 'YELLOW' as const, risk_score: 0.2 }
    expect(alertLevelFromPatient(yellow)).toBe('YELLOW')
  })
})

describe('sceneStore', () => {
  beforeEach(() => {
    useSceneStore.setState({
      selectedPatientId: null,
      selectedPatient: null,
      panelOpen: false,
      sceneMode: 'overview',
      alertPulse: false,
      lastAlertPatientId: null,
    })
  })

  it('opens patient panel', () => {
    useSceneStore.getState().openPanel(mockPatient)
    expect(useSceneStore.getState().panelOpen).toBe(true)
    expect(useSceneStore.getState().selectedPatientId).toBe('37464')
  })

  it('closes panel', () => {
    useSceneStore.getState().openPanel(mockPatient)
    useSceneStore.getState().closePanel()
    expect(useSceneStore.getState().panelOpen).toBe(false)
  })

  it('triggers alert pulse', () => {
    useSceneStore.getState().triggerAlertPulse('37464')
    expect(useSceneStore.getState().alertPulse).toBe(true)
    expect(useSceneStore.getState().lastAlertPatientId).toBe('37464')
  })

  it('sets scene mode', () => {
    useSceneStore.getState().setSceneMode('icu')
    expect(useSceneStore.getState().sceneMode).toBe('icu')
  })
})

describe('PatientIntelligencePanel', () => {
  it('renders patient data when open', () => {
    render(
      <PatientIntelligencePanel
        patient={mockPatient}
        open={true}
        onClose={vi.fn()}
        connected={true}
      />,
    )
    expect(screen.getByText('Patient #37464')).toBeInTheDocument()
    expect(screen.getByText(/85\.0%/)).toBeInTheDocument()
    expect(screen.getByText('High')).toBeInTheDocument()
    expect(screen.getByText(/Urgent clinician review/)).toBeInTheDocument()
  })

  it('shows vitals', () => {
    render(
      <PatientIntelligencePanel
        patient={mockPatient}
        open={true}
        onClose={vi.fn()}
      />,
    )
    expect(screen.getByText('110 bpm')).toBeInTheDocument()
    expect(screen.getByText('91%')).toBeInTheDocument()
  })

  it('calls onClose when X clicked', () => {
    const onClose = vi.fn()
    render(
      <PatientIntelligencePanel
        patient={mockPatient}
        open={true}
        onClose={onClose}
      />,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(onClose).toHaveBeenCalled()
  })

  it('hidden when closed', () => {
    render(
      <PatientIntelligencePanel
        patient={mockPatient}
        open={false}
        onClose={vi.fn()}
      />,
    )
    expect(screen.queryByText('Patient #37464')).not.toBeInTheDocument()
  })
})

describe('3D routes', () => {
  it('defines digital twin route', () => {
    expect(ROUTES.digitalTwin).toBe('/digital-twin')
  })

  it('defines executive 3d route', () => {
    expect(ROUTES.executive3d).toBe('/executive-3d')
  })

  it('defines patient 3d route prefix', () => {
    expect(ROUTES.patient3d).toBe('/patient-3d')
  })
})

describe('SceneCanvas mock', () => {
  it('renders canvas wrapper', async () => {
    const { SceneCanvas } = await import('@/three/components/canvas/SceneCanvas')
    render(
      <SceneCanvas>
        <mesh />
      </SceneCanvas>,
    )
    expect(screen.getByTestId('r3f-canvas')).toBeInTheDocument()
  })
})

describe('SceneHUD', () => {
  it('renders HUD with live indicator', async () => {
    const { SceneHUD } = await import('@/three/components/ui/SceneHUD')
    render(
      <MemoryRouter>
        <SceneHUD
          title="Hospital Digital Twin"
          connected={true}
          executive={{
            current_icu_patients: 5,
            high_risk_count: 2,
            critical_alert_count: 1,
            black_alert_count: 0,
            average_risk_score: 0.4,
            predictions_today: 100,
            alerts_today: 10,
            model_accuracy: 0.95,
            system_uptime_seconds: 3600,
            top_critical: [],
            top_escalating: [],
            top_stable: [],
          }}
        />
      </MemoryRouter>,
    )
    expect(screen.getByText('Hospital Digital Twin')).toBeInTheDocument()
    expect(screen.getByText(/Live Stream/)).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })
})
