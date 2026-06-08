import { create } from 'zustand'
import type { PatientFeatures, PredictResponse } from '@/api/types'

interface PatientState {
  selectedPatientId: string | null
  lastPrediction: PredictResponse | null
  monitoredPatients: string[]
  setSelectedPatient: (id: string | null) => void
  setLastPrediction: (result: PredictResponse | null) => void
  addMonitoredPatient: (id: string) => void
  removeMonitoredPatient: (id: string) => void
}

export const usePatientStore = create<PatientState>((set, get) => ({
  selectedPatientId: null,
  lastPrediction: null,
  monitoredPatients: [],
  setSelectedPatient: (id) => set({ selectedPatientId: id }),
  setLastPrediction: (result) => set({ lastPrediction: result }),
  addMonitoredPatient: (id) => {
    const current = get().monitoredPatients
    if (!current.includes(id)) {
      set({ monitoredPatients: [...current, id] })
    }
  },
  removeMonitoredPatient: (id) =>
    set({ monitoredPatients: get().monitoredPatients.filter((p) => p !== id) }),
}))

export type { PatientFeatures }
