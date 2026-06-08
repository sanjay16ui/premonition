import { useCallback, useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  createSSEConnection,
  fetchExecutiveSummary,
  fetchLivePatients,
  fetchPriorityRanking,
} from '../realtime'
import type { ExecutiveSummary, PatientMonitorState } from '../types'
import { audioManager } from '@/utils/audio'

export interface AgentAction {
  patient_id: string
  event: string
  explanation?: {
    agent: string
    reason: string
    action: string
    confidence: string
  }
  recommendations?: string[]
}

export function useExecutiveSummary() {
  return useQuery({
    queryKey: ['executive'],
    queryFn: fetchExecutiveSummary,
    refetchInterval: 10_000,
  })
}

export function useLivePatients() {
  return useQuery({
    queryKey: ['livePatients'],
    queryFn: fetchLivePatients,
    refetchInterval: 8_000,
  })
}

export function usePriorityRanking() {
  return useQuery({
    queryKey: ['priority'],
    queryFn: fetchPriorityRanking,
    refetchInterval: 10_000,
  })
}

export function useRealtimeStream() {
  const [patients, setPatients] = useState<Record<string, PatientMonitorState>>({})
  const [executive, setExecutive] = useState<ExecutiveSummary | null>(null)
  const [alerts, setAlerts] = useState<unknown[]>([])
  const [agentActions, setAgentActions] = useState<AgentAction[]>([])
  const [connected, setConnected] = useState(false)
  const sourceRef = useRef<EventSource | null>(null)
  const lastSoundRef = useRef<number>(0)

  const handleEvent = useCallback((eventType: string, data: unknown) => {
    if (eventType === 'connected') setConnected(true)
    if (eventType === 'patient_update') {
      const payload = data as { patient?: PatientMonitorState }
      if (payload.patient) {
        setPatients((prev) => ({
          ...prev,
          [payload.patient!.patient_id]: payload.patient!,
        }))
      }
    }
    if (eventType === 'executive_summary') {
      setExecutive(data as ExecutiveSummary)
    }
    if (eventType === 'alert' || eventType === 'alerts') {
      setAlerts((prev) => [data, ...prev].slice(0, 50))
      // Trigger audio alert with debounce (max 1 sound per 5s)
      const now = Date.now()
      if (now - lastSoundRef.current > 5000) {
        const alertData = data as { alert_level?: string }
        const level = alertData?.alert_level as 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED' | 'BLACK' | undefined
        if (level) {
          audioManager.play(level)
          lastSoundRef.current = now
        }
      }
    }
    if (eventType === 'agent_action') {
      setAgentActions((prev) => [data as AgentAction, ...prev].slice(0, 100))
    }
  }, [])

  useEffect(() => {
    sourceRef.current = createSSEConnection(handleEvent)
    return () => {
      sourceRef.current?.close()
    }
  }, [handleEvent])

  return {
    connected,
    patients: Object.values(patients),
    executive,
    recentAlerts: alerts,
    agentActions,
  }
}
