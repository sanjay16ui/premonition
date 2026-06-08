import { useState, useEffect, useRef, useCallback } from 'react'
import { RefreshCw, Radio, UserPlus, AlertTriangle, Clock, ChevronUp } from 'lucide-react'
import { useLivePatients, useRealtimeStream } from '@/api/hooks/realtime'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { LoadingOverlay } from '@/components/common/LoadingOverlay'
import { EmptyState } from '@/components/ui/EmptyState'
import { formatRelativeTime } from '@/utils/format'
import { Link } from 'react-router-dom'
import { ROUTES } from '@/routes/paths'
import type { PatientMonitorState } from '@/api/types'
import { useAlertAudio } from '@/hooks/useAlertAudio'
import { motion, AnimatePresence } from 'framer-motion'
import { audioManager } from '@/utils/audio'

export function AudioUnlocker() {
  useEffect(() => {
    const unlock = () => {
      audioManager.resumeContext();
      window.removeEventListener('click', unlock);
      window.removeEventListener('keydown', unlock);
    };
    window.addEventListener('click', unlock);
    window.addEventListener('keydown', unlock);
    return () => {
      window.removeEventListener('click', unlock);
      window.removeEventListener('keydown', unlock);
    };
  }, []);
  return null;
}

const DOCTOR_STATUS = {
  GREEN:  { label: 'Stable',     bg: 'bg-emerald-500/10', border: 'border-emerald-500/40', text: 'text-emerald-400',  icon: '🟢', glow: '' },
  YELLOW: { label: 'Watch',      bg: 'bg-amber-500/10',   border: 'border-amber-500/40',   text: 'text-amber-400',    icon: '🟡', glow: '' },
  ORANGE: { label: 'High Risk',  bg: 'bg-orange-500/10',  border: 'border-orange-500/40',  text: 'text-orange-400',   icon: '🟠', glow: '' },
  RED:    { label: 'CRITICAL',   bg: 'bg-red-900/20',     border: 'border-red-500',        text: 'text-red-400',      icon: '🔴', glow: 'shadow-[0_0_20px_rgba(239,68,68,0.3)]' },
  BLACK:  { label: 'EMERGENCY',  bg: 'bg-slate-800',      border: 'border-white/30',       text: 'text-white',        icon: '⚫', glow: 'shadow-[0_0_30px_rgba(255,255,255,0.1)]' },
}

interface EscalationState {
  patient: PatientMonitorState
  startTime: number
  level: 1 | 2 | 3
  escalationLog: Array<{ level: number; time: string; target: string }>
}

// ─── Emergency Alert Modal ─────────────────────────────────────────────────────
function EmergencyModal({ escalation, onAcknowledge }: { escalation: EscalationState; onAcknowledge: () => void }) {
  const [elapsed, setElapsed] = useState(0)
  const p = escalation.patient
  const status = DOCTOR_STATUS[p.alert_level as keyof typeof DOCTOR_STATUS] || DOCTOR_STATUS.RED

  useEffect(() => {
    const iv = setInterval(() => setElapsed(Math.floor((Date.now() - escalation.startTime) / 1000)), 1000)
    return () => clearInterval(iv)
  }, [escalation.startTime])

  const recommendation = p.recommendations?.[0]?.text || 'Immediate clinical assessment required. Check vitals, prepare emergency intervention.'
  const alertReason = p.active_alerts?.[0]?.reason || `Patient ${p.patient_id} reached ${p.alert_level} — risk ${(p.risk_score * 100).toFixed(1)}%`
  const levelLabel = escalation.level === 1 ? 'Awaiting Acknowledgement' : escalation.level === 2 ? '⚠ Escalated to Doctor' : '🚨 Escalated to ICU Lead'
  const levelColor = escalation.level === 1 ? 'text-red-400' : escalation.level === 2 ? 'text-orange-400' : 'text-white'

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="relative mx-4 w-full max-w-lg rounded-2xl border border-red-500/50 bg-slate-900 shadow-[0_0_60px_rgba(239,68,68,0.4)] overflow-hidden"
      >
        <div className="h-1.5 w-full bg-red-500 animate-pulse" />
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-500/20 border border-red-500/50 animate-pulse">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-red-400 uppercase tracking-widest">Emergency Alert</h2>
                <p className="text-xs text-slate-400">Patient #{p.patient_id} · {status.label}</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5 rounded-full bg-slate-800 px-3 py-1">
              <Clock className="h-3 w-3 text-slate-400" />
              <span className="text-xs font-mono text-slate-300">{Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}</span>
            </div>
          </div>

          <div className={`mb-4 text-xs font-bold uppercase tracking-widest ${levelColor}`}>{levelLabel}</div>

          <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/20 p-4">
            <p className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-1">Alert Trigger</p>
            <p className="text-sm text-slate-200">{alertReason}</p>
          </div>

          <div className="mb-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-slate-800 p-3">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Sepsis Risk</p>
              <p className="text-2xl font-bold text-red-400 font-mono">{(p.risk_score * 100).toFixed(1)}%</p>
            </div>
            <div className="rounded-xl bg-slate-800 p-3">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Confidence</p>
              <p className="text-2xl font-bold text-slate-200 font-mono">{p.confidence}</p>
            </div>
          </div>

          {p.vitals && (
            <div className="mb-4 grid grid-cols-4 gap-2">
              {([['HR', p.vitals.hr_mean?.toFixed(0), 'bpm'], ['SpO2', p.vitals.spo2_mean?.toFixed(0), '%'], ['Temp', p.vitals.temp_celsius_mean?.toFixed(1), '°C'], ['RR', p.vitals.respiratory_rate_mean?.toFixed(0), '/min']] as [string, string, string][]).map(([label, val, unit]) => (
                <div key={label} className="rounded-lg bg-slate-800/60 p-2 text-center">
                  <p className="text-[9px] text-slate-500 uppercase">{label}</p>
                  <p className="text-sm font-bold font-mono text-slate-200">{val}<span className="text-[9px] text-slate-500">{unit}</span></p>
                </div>
              ))}
            </div>
          )}

          <div className="mb-6 rounded-xl bg-sky-500/10 border border-sky-500/20 p-4">
            <p className="text-xs font-semibold text-sky-400 uppercase tracking-wider mb-2">🤖 AI Recommendation</p>
            <p className="text-sm text-sky-300">{recommendation}</p>
          </div>

          {escalation.escalationLog.length > 0 && (
            <div className="mb-4">
              {escalation.escalationLog.map((log, i) => (
                <div key={i} className="text-xs text-slate-500 mb-1">• Level {log.level} escalated to {log.target} at {log.time}</div>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <button
              id="emergency-acknowledge-btn"
              onClick={onAcknowledge}
              className="flex-1 rounded-xl bg-red-500 hover:bg-red-600 text-white font-bold py-3 transition-all duration-150 shadow-lg shadow-red-500/30"
            >
              ✓ Acknowledge & Stop Alert
            </button>
            <Link to={ROUTES.copilot} className="flex-1">
              <button className="w-full rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold py-3 transition-all duration-150">
                Ask Copilot
              </button>
            </Link>
          </div>
        </div>
        <div className="h-1.5 w-full bg-red-500 animate-pulse" />
      </motion.div>
    </motion.div>
  )
}

// ─── AI Recommendation Panel ──────────────────────────────────────────────────
function AIRecommendationPanel({ p }: { p: PatientMonitorState }) {
  const recs = p.recommendations || []
  const alerts = p.active_alerts || []
  const status = DOCTOR_STATUS[p.alert_level as keyof typeof DOCTOR_STATUS] || DOCTOR_STATUS.GREEN
  const riskPct = (p.risk_score * 100).toFixed(1)

  return (
    <div className="mt-4 rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">🤖 AI Recommendation Panel</p>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <p className="text-[9px] text-slate-500 uppercase">Risk Level</p>
          <p className={`text-sm font-bold ${status.text}`}>{status.label}</p>
        </div>
        <div>
          <p className="text-[9px] text-slate-500 uppercase">Risk Score</p>
          <p className="text-sm font-bold font-mono text-slate-200">{riskPct}%</p>
        </div>
      </div>
      {alerts.length > 0 && (
        <div className="mb-3">
          <p className="text-[9px] text-slate-500 uppercase mb-1">Risk Factors</p>
          {alerts.slice(0, 3).map((a, i) => (
            <p key={i} className="text-xs text-red-400 mb-0.5">• {a.reason || (a as any).message}</p>
          ))}
        </div>
      )}
      {recs.length > 0 && (
        <div>
          <p className="text-[9px] text-slate-500 uppercase mb-1">Recommended Actions</p>
          {recs.slice(0, 3).map((r, i) => (
            <p key={i} className="text-xs text-sky-400 mb-0.5">→ {r.text}</p>
          ))}
        </div>
      )}
      {recs.length === 0 && alerts.length === 0 && (
        <p className="text-xs text-slate-500">Continue standard monitoring protocol.</p>
      )}
    </div>
  )
}

// ─── Patient Card ──────────────────────────────────────────────────────────────
function LivePatientCard({ p, showDetails, onCriticalClick, isAcknowledged = false }: { p: PatientMonitorState; showDetails: boolean; onCriticalClick: () => void; isAcknowledged?: boolean }) {
  const status = DOCTOR_STATUS[p.alert_level as keyof typeof DOCTOR_STATUS] || DOCTOR_STATUS.GREEN
  const happened = p.active_alerts?.[0]?.reason || 'Vitals within normal limits.'
  const why = p.recommendations?.[0]?.reason || 'No active risk drivers detected.'
  const nextStep = p.recommendations?.[0]?.text || 'Continue standard monitoring.'
  const [isAcknowledging, setIsAcknowledging] = useState(false)
  const isGreen = p.alert_level === 'GREEN'
  // Immediately stop flashing if acknowledged, even before next server poll
  const isFlashing = !isAcknowledged && (p.alert_level === 'RED' || p.alert_level === 'BLACK')

  const handleAcknowledge = async () => {
    setIsAcknowledging(true)
    try {
      const { acknowledgePatient } = await import('@/api/realtime')
      await acknowledgePatient(p.patient_id)
    } catch (e) {
      console.error('Failed to acknowledge', e)
    } finally {
      setIsAcknowledging(false)
    }
  }

  return (
    <motion.div layout>
      <GlassCard className={`border-l-4 ${isAcknowledged ? 'border-emerald-500/40' : status.border} ${isAcknowledged ? '' : status.glow} ${isFlashing ? 'ring-1 ring-red-500/50' : ''}`}>
        {isFlashing && (
          <div className="mb-3 flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2">
            <Radio className="h-3 w-3 text-red-400 animate-ping" />
            <span className="text-xs font-bold text-red-400 uppercase">Critical — Requires Immediate Attention</span>
            <button onClick={onCriticalClick} className="ml-auto text-xs text-red-300 underline hover:text-red-200">View Alert</button>
          </div>
        )}
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xl font-bold flex items-center gap-2">
              Patient #{p.patient_id} <span className="text-sm font-normal text-slate-400">Bed {p.patient_id.substring(0, 3)}</span>
            </p>
            <p className="text-xs text-slate-400 mt-1">Updated {formatRelativeTime(p.last_updated)}</p>
          </div>
          <div className={`px-3 py-1 rounded-full flex items-center gap-2 ${status.bg} ${status.text} font-bold text-sm`}>
            {status.icon} {status.label}
          </div>
        </div>

        <div className="mt-4 space-y-3">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Alert</p>
            <p className="text-sm font-medium text-slate-200">{happened}</p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Clinical Reason</p>
            <p className="text-sm text-slate-300">{why}</p>
          </div>
          <div className="bg-sky-500/10 rounded-lg p-3 border border-sky-500/20">
            <p className="text-xs font-semibold text-sky-500 uppercase tracking-wider mb-1">Recommended Action</p>
            <p className="text-sm font-bold text-sky-400">{nextStep}</p>
            <div className="mt-3 flex gap-2">
              <Button variant="primary" onClick={handleAcknowledge} disabled={isGreen || isAcknowledging}>
                {isGreen ? 'Acknowledged' : isAcknowledging ? 'Acknowledging…' : 'Acknowledge'}
              </Button>
              <Link to={ROUTES.copilotPatient.replace(':id', p.patient_id)}>
                <Button variant="secondary">Ask Copilot</Button>
              </Link>
            </div>
          </div>
        </div>

        <AIRecommendationPanel p={p} />

        {showDetails && (
          <div className="mt-4 pt-4 border-t border-white/5 space-y-3">
            <p className="text-xs font-semibold text-slate-400">Advanced Details</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] text-slate-500 uppercase">ML Risk Score</p>
                <p className="text-lg font-mono text-slate-300">{(p.risk_score * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase">Model Confidence</p>
                <p className="text-lg font-mono text-slate-300">{p.confidence}</p>
              </div>
            </div>
            {p.vitals && (
              <div className="grid grid-cols-4 gap-2 text-xs font-mono text-slate-400 bg-black/20 p-2 rounded">
                <div>HR: {p.vitals.hr_mean.toFixed(0)}</div>
                <div>SpO2: {p.vitals.spo2_mean.toFixed(0)}%</div>
                <div>Temp: {p.vitals.temp_celsius_mean.toFixed(1)}</div>
                <div>Resp: {p.vitals.respiratory_rate_mean.toFixed(0)}</div>
              </div>
            )}
          </div>
        )}
      </GlassCard>
    </motion.div>
  )
}

// ─── Critical Patient Spotlight ───────────────────────────────────────────────
function CriticalSpotlight({ patient }: { patient: PatientMonitorState }) {
  const status = DOCTOR_STATUS[patient.alert_level as keyof typeof DOCTOR_STATUS] || DOCTOR_STATUS.RED
  return (
    <div className="mb-6 rounded-2xl border border-red-500/50 bg-gradient-to-r from-red-950/60 to-slate-900 p-5 shadow-[0_0_30px_rgba(239,68,68,0.2)]">
      <div className="flex items-center gap-3 mb-3">
        <ChevronUp className="h-5 w-5 text-red-400 animate-bounce" />
        <span className="text-xs font-bold text-red-400 uppercase tracking-widest">Critical Patient Spotlight</span>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-2xl font-bold text-white">Patient #{patient.patient_id}</p>
          <p className={`text-sm font-semibold ${status.text}`}>{status.label} · {(patient.risk_score * 100).toFixed(1)}% Sepsis Risk</p>
          {patient.active_alerts?.[0] && (
            <p className="text-xs text-red-300 mt-1">{patient.active_alerts[0].reason}</p>
          )}
        </div>
        {patient.vitals && (
          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-right">
            <div><span className="text-[10px] text-slate-500 uppercase">HR </span><span className="text-sm font-mono text-slate-200">{patient.vitals.hr_mean.toFixed(0)} bpm</span></div>
            <div><span className="text-[10px] text-slate-500 uppercase">SpO2 </span><span className="text-sm font-mono text-slate-200">{patient.vitals.spo2_mean.toFixed(0)}%</span></div>
            <div><span className="text-[10px] text-slate-500 uppercase">Temp </span><span className="text-sm font-mono text-slate-200">{patient.vitals.temp_celsius_mean.toFixed(1)}°C</span></div>
            <div><span className="text-[10px] text-slate-500 uppercase">RR </span><span className="text-sm font-mono text-slate-200">{patient.vitals.respiratory_rate_mean.toFixed(0)}/min</span></div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export function LiveMonitoringPage() {
  const { data, isLoading, refetch, isFetching } = useLivePatients()
  const { connected, patients: streamPatients } = useRealtimeStream()
  const [filter, setFilter] = useState<'all' | 'alerts'>('all')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [activeEscalation, setActiveEscalation] = useState<EscalationState | null>(null)
  const escalationTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const escalationLevel3Timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const prevCritical = useRef<Set<string>>(new Set())

  const patients: PatientMonitorState[] = streamPatients.length > 0 ? streamPatients : (data || [])

  useAlertAudio(patients)

  // Detect new critical patients → trigger emergency modal
  useEffect(() => {
    const criticalNow = patients.filter(p => p.alert_level === 'RED' || p.alert_level === 'BLACK')
    const newCritical = criticalNow.filter(p => !prevCritical.current.has(p.patient_id))

    if (newCritical.length > 0 && !activeEscalation) {
      const worst = [...newCritical].sort((a, b) => b.risk_score - a.risk_score)[0]
      setActiveEscalation({ patient: worst, startTime: Date.now(), level: 1, escalationLog: [] })
    }

    criticalNow.forEach(p => prevCritical.current.add(p.patient_id))
    patients.filter(p => p.alert_level === 'GREEN' || p.alert_level === 'YELLOW')
      .forEach(p => prevCritical.current.delete(p.patient_id))
  }, [patients])

  // Escalation timers: Level 2 @ 60s, Level 3 @ 5min
  useEffect(() => {
    if (!activeEscalation) return

    escalationTimer.current = setTimeout(() => {
      setActiveEscalation(prev => {
        if (!prev) return null
        const log = { level: 2, time: new Date().toLocaleTimeString(), target: 'Doctor' }
        console.warn(`[ESCALATION L2] Patient ${prev.patient.patient_id} escalated to Doctor at ${log.time}`)
        return { ...prev, level: 2, escalationLog: [...prev.escalationLog, log] }
      })
    }, 60_000)

    escalationLevel3Timer.current = setTimeout(() => {
      setActiveEscalation(prev => {
        if (!prev) return null
        const log = { level: 3, time: new Date().toLocaleTimeString(), target: 'ICU Lead' }
        console.error(`[ESCALATION L3] Patient ${prev.patient.patient_id} escalated to ICU Lead at ${log.time}`)
        return { ...prev, level: 3, escalationLog: [...prev.escalationLog, log] }
      })
    }, 300_000)

    return () => {
      if (escalationTimer.current) clearTimeout(escalationTimer.current)
      if (escalationLevel3Timer.current) clearTimeout(escalationLevel3Timer.current)
    }
  }, [activeEscalation?.patient?.patient_id])

  const [acknowledgedPatients, setAcknowledgedPatients] = useState<Set<string>>(new Set())

  const handleAcknowledge = useCallback(async () => {
    // 1. Stop alarm immediately
    audioManager.stopAll()
    // 2. Clear escalation timers
    if (escalationTimer.current) clearTimeout(escalationTimer.current)
    if (escalationLevel3Timer.current) clearTimeout(escalationLevel3Timer.current)

    if (activeEscalation) {
      const pid = activeEscalation.patient.patient_id

      // 3. Store acknowledgement timestamp + clinician in localStorage
      const ackRecord = {
        patient_id: pid,
        acknowledged_at: new Date().toISOString(),
        clinician: localStorage.getItem('premonition_email') || 'demo@premonition.health',
        risk_score: activeEscalation.patient.risk_score,
        level: activeEscalation.level,
      }
      const existing = JSON.parse(localStorage.getItem('premonition_ack_log') || '[]')
      localStorage.setItem('premonition_ack_log', JSON.stringify([ackRecord, ...existing].slice(0, 50)))

      // 4. Immediately remove red banner + critical state in UI (don't wait for refetch)
      setAcknowledgedPatients(prev => new Set([...prev, pid]))
      prevCritical.current.delete(pid)

      // 5. Background API call + refetch
      try {
        const { acknowledgePatient } = await import('@/api/realtime')
        await acknowledgePatient(pid)
        refetch()
      } catch (e) {
        console.error('Acknowledge API failed (UI already updated):', e)
      }

      setToastMsg(`Alert for Patient #${pid} acknowledged`)
      setTimeout(() => setToastMsg(null), 3000)
    }

    // 6. Close popup immediately
    setActiveEscalation(null)
  }, [activeEscalation, refetch])


  if (isLoading && patients.length === 0) {
    return <LoadingOverlay label="Connecting to live ICU stream..." />
  }

  const [toastMsg, setToastMsg] = useState<string | null>(null)

  const filtered = filter === 'alerts' ? patients.filter(p => p.alert_level !== 'GREEN') : patients
  // Remove acknowledged patients from red-state views immediately
  const criticalPatients = patients.filter(p =>
    (p.alert_level === 'RED' || p.alert_level === 'BLACK') && !acknowledgedPatients.has(p.patient_id)
  )
  const spotlightPatient = [...criticalPatients].sort((a, b) => b.risk_score - a.risk_score)[0]

  return (
    <PageContainer
      title="Live Patient Monitoring"
      subtitle="Real-time ICU surveillance powered by Agentic AI · Emergency escalation active"
      action={
        <div className="flex items-center gap-3">
          <span className={`flex items-center gap-1.5 text-xs ${connected ? 'text-emerald-500' : 'text-slate-400'}`}>
            <Radio className={`h-3 w-3 ${connected ? 'animate-pulse' : ''}`} />
            {connected ? 'Live Stream' : 'Polling'}
          </span>
          <Button variant="secondary" onClick={() => setShowAdvanced(!showAdvanced)}>
            {showAdvanced ? 'Hide Details' : 'Show Details'}
          </Button>
          <Button
            variant="primary"
            icon={<RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        </div>
      }
    >
      {/* Emergency Modal */}
      <AnimatePresence>
        {activeEscalation && <EmergencyModal escalation={activeEscalation} onAcknowledge={handleAcknowledge} />}
      </AnimatePresence>

      {/* Critical Spotlight */}
      {spotlightPatient && <CriticalSpotlight patient={spotlightPatient} />}

      {/* Emergency Banner */}
      {criticalPatients.length > 0 && (
        <div className="mb-6 rounded-lg bg-red-500/10 border border-red-500/30 p-4 shadow-[0_0_15px_rgba(239,68,68,0.2)] animate-pulse">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-red-500 p-2 text-white">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-red-500 uppercase tracking-widest">Emergency Alert Active</h3>
                <p className="text-xs text-red-400">{criticalPatients.length} patient(s) requiring immediate intervention.</p>
              </div>
            </div>
            <button
              id="view-emergency-btn"
              onClick={() => criticalPatients[0] && setActiveEscalation({ patient: criticalPatients[0], startTime: Date.now(), level: 1, escalationLog: [] })}
              className="rounded-lg bg-red-500 px-4 py-2 text-xs font-bold text-white hover:bg-red-600 transition-colors"
            >
              View Emergency
            </button>
          </div>
        </div>
      )}

      {/* Filter Buttons */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${filter === 'all' ? 'bg-sky-500 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'}`}
        >
          All Patients ({patients.length})
        </button>
        <button
          onClick={() => setFilter('alerts')}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${filter === 'alerts' ? 'bg-red-500 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'}`}
        >
          High Risk / Critical ({patients.filter(p => p.alert_level !== 'GREEN').length})
        </button>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="Waiting for live data"
          description="The realtime engine simulates ICU vitals every few seconds. Data will appear shortly."
          action={
            <Link to={ROUTES.patientRisk}>
              <Button icon={<UserPlus className="h-4 w-4" />}>Run Manual Prediction</Button>
            </Link>
          }
        />
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map(p => (
            <LivePatientCard
              key={p.patient_id}
              p={p}
              showDetails={showAdvanced}
              isAcknowledged={acknowledgedPatients.has(p.patient_id)}
              onCriticalClick={() => setActiveEscalation({ patient: p, startTime: Date.now(), level: 1, escalationLog: [] })}
            />
          ))}
        </div>
      )}
      {toastMsg && (
        <div className="fixed bottom-4 right-4 z-[200] rounded-xl bg-emerald-500 px-6 py-3 text-sm font-bold text-white shadow-lg">
          {toastMsg}
        </div>
      )}

      <AudioUnlocker />
    </PageContainer>
  )
}
