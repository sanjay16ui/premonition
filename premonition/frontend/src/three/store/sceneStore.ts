import { create } from 'zustand'
import type { PatientMonitorState } from '@/api/types'

export type SceneMode = 'overview' | 'icu' | 'command' | 'dataflow' | 'patient'

interface SceneState {
  selectedPatientId: string | null
  selectedPatient: PatientMonitorState | null
  panelOpen: boolean
  sceneMode: SceneMode
  alertPulse: boolean
  lastAlertPatientId: string | null
  setSelectedPatient: (patient: PatientMonitorState | null) => void
  openPanel: (patient: PatientMonitorState) => void
  closePanel: () => void
  setSceneMode: (mode: SceneMode) => void
  triggerAlertPulse: (patientId: string) => void
}

export const useSceneStore = create<SceneState>((set) => ({
  selectedPatientId: null,
  selectedPatient: null,
  panelOpen: false,
  sceneMode: 'overview',
  alertPulse: false,
  lastAlertPatientId: null,
  setSelectedPatient: (patient) =>
    set({
      selectedPatient: patient,
      selectedPatientId: patient?.patient_id ?? null,
    }),
  openPanel: (patient) =>
    set({
      selectedPatient: patient,
      selectedPatientId: patient.patient_id,
      panelOpen: true,
    }),
  closePanel: () => set({ panelOpen: false }),
  setSceneMode: (mode) => set({ sceneMode: mode }),
  triggerAlertPulse: (patientId) =>
    set({ alertPulse: true, lastAlertPatientId: patientId }),
}))
