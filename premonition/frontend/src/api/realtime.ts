/** Realtime streaming client — SSE and WebSocket */

import { apiClient } from './client'
import type { ExecutiveSummary, PatientMonitorState, PriorityRanking } from './types'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export type RealtimeEventHandler = (eventType: string, data: unknown) => void

function getAuthQuery() {
  const apiKey = import.meta.env.VITE_API_KEY || ''
  const token = localStorage.getItem('premonition_access_token') || ''
  const params = new URLSearchParams()
  if (apiKey) params.append('api_key', apiKey)
  if (token) params.append('token', token)
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function createSSEConnection(onEvent: RealtimeEventHandler): EventSource {
  const url = `${baseURL}/realtime/stream${getAuthQuery()}`
  const source = new EventSource(url)

  const safeParse = (data: string) => {
    try {
      return JSON.parse(data)
    } catch (e) {
      console.warn('Skipping malformed SSE frame:', e)
      return null
    }
  }

  source.addEventListener('connected', (e) => {
    const data = safeParse((e as MessageEvent).data)
    if (data) onEvent('connected', data)
  })

  source.addEventListener('patient_update', (e) => {
    const data = safeParse((e as MessageEvent).data)
    if (data) onEvent('patient_update', data)
  })

  source.addEventListener('alert', (e) => {
    const data = safeParse((e as MessageEvent).data)
    if (data) onEvent('alert', data)
  })

  source.addEventListener('alerts', (e) => {
    const data = safeParse((e as MessageEvent).data)
    if (data) onEvent('alerts', data)
  })

  source.addEventListener('executive_summary', (e) => {
    const data = safeParse((e as MessageEvent).data)
    if (data) onEvent('executive_summary', data)
  })

  source.addEventListener('early_warning', (e) => {
    const data = safeParse((e as MessageEvent).data)
    if (data) onEvent('early_warning', data)
  })

  source.addEventListener('heartbeat', () => {
    onEvent('heartbeat', { ts: 'ping' })
  })

  source.onerror = () => {
    onEvent('error', { message: 'SSE connection error' })
  }

  return source
}

export function createWebSocket(onMessage: RealtimeEventHandler): WebSocket {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const url = `${wsProtocol}//${host}${baseURL}/realtime/ws${getAuthQuery()}`
  const ws = new WebSocket(url)

  ws.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data)
      onMessage(parsed.event_type || parsed.event || 'message', parsed)
    } catch {
      onMessage('raw', event.data)
    }
  }

  ws.onopen = () => {
    ws.send(JSON.stringify({ action: 'subscribe_all' }))
  }

  return ws
}

export async function fetchExecutiveSummary(): Promise<ExecutiveSummary> {
  const res = await apiClient.get<ExecutiveSummary>('/realtime/executive')
  return res.data
}

export async function fetchLivePatients(): Promise<PatientMonitorState[]> {
  const res = await apiClient.get<PatientMonitorState[]>('/realtime/patients')
  return res.data
}

export async function fetchPriorityRanking(): Promise<PriorityRanking> {
  const res = await apiClient.get<PriorityRanking>('/realtime/priority')
  return res.data
}

export async function acknowledgePatient(patientId: string): Promise<void> {
  await apiClient.post(`/realtime/patients/${patientId}/acknowledge`)
}
