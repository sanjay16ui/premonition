import { useEffect, useMemo } from 'react'
import { useLivePatients, useRealtimeStream, useExecutiveSummary } from '@/api/hooks/realtime'
import { useSceneStore } from '@/three/store/sceneStore'
import type { PatientMonitorState } from '@/api/types'

export function useScenePatients() {
  const { data: restPatients, isLoading } = useLivePatients()
  const { patients: streamPatients, executive: streamExec, connected, recentAlerts, agentActions } =
    useRealtimeStream()
  const { data: restExec } = useExecutiveSummary()
  const triggerAlertPulse = useSceneStore((s) => s.triggerAlertPulse)

  const patients: PatientMonitorState[] = useMemo(() => {
    if (streamPatients.length > 0) return streamPatients
    return restPatients ?? []
  }, [streamPatients, restPatients])

  const executive = streamExec || restExec || null

  useEffect(() => {
    if (recentAlerts.length > 0) {
      const latest = recentAlerts[0] as { patient_id?: string }
      if (latest?.patient_id) {
        triggerAlertPulse(latest.patient_id)
      }
    }
  }, [recentAlerts, triggerAlertPulse])

  return {
    patients,
    executive,
    connected,
    isLoading: isLoading && patients.length === 0,
    recentAlerts,
    agentActions,
  }
}
