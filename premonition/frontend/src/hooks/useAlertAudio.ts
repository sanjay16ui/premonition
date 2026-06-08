/**
 * useAlertAudio
 *
 * Watches a list of live patients and fires Web Audio API tones whenever
 * a patient's alert level *escalates* (moves to a higher severity tier).
 * Plays the highest active alert level at most once every 6 seconds to
 */
import { useEffect, useRef } from 'react'
import { audioManager } from '@/utils/audio'
import type { PatientMonitorState } from '@/api/types'
export function useAlertAudio(patients: PatientMonitorState[]) {
  const prevLevels = useRef<Record<string, string>>({})

  useEffect(() => {
    if (!patients.length) return

    let shouldPlaySiren = false

    for (const patient of patients) {
      const pAny = patient as any
      const isCritical =
        patient.risk_score >= 0.90 ||
        patient.alert_level === 'RED' ||
        patient.alert_level === 'BLACK' ||
        pAny.sepsis_probability >= 0.90

      if (isCritical) {
        if (prevLevels.current[patient.patient_id] !== 'TRIGGERED') {
          shouldPlaySiren = true
          prevLevels.current[patient.patient_id] = 'TRIGGERED'
        }
      } else {
        prevLevels.current[patient.patient_id] = 'SAFE'
      }
    }

    if (shouldPlaySiren) {
      audioManager.setVolume(1.0)
      audioManager.play('BLACK') // BLACK is the siren
    }
  }, [patients])
}
