import { motion, AnimatePresence } from 'framer-motion'
import { X, Activity, Heart, Thermometer, Wind, Droplets } from 'lucide-react'
import type { PatientMonitorState } from '@/api/types'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { alertLevelFromPatient, RISK_COLORS } from '@/three/utils/riskColors'
import { formatPercent } from '@/utils/format'

interface PatientIntelligencePanelProps {
  patient: PatientMonitorState | null
  open: boolean
  onClose: () => void
  connected?: boolean
}

const ALERT_LABELS: Record<string, string> = {
  GREEN: 'Normal',
  YELLOW: 'Monitor Closely',
  ORANGE: 'High Risk',
  RED: 'Critical',
  BLACK: 'Immediate Intervention',
}

export function PatientIntelligencePanel({
  patient,
  open,
  onClose,
  connected,
}: PatientIntelligencePanelProps) {
  if (!patient) return null

  const level = alertLevelFromPatient(patient)
  const color = RISK_COLORS[level]

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25 }}
          className="absolute right-0 top-0 z-50 h-full w-96 max-w-full overflow-y-auto border-l border-slate-700/50 bg-slate-950/90 backdrop-blur-xl"
        >
          <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-700/50 bg-slate-950/95 px-5 py-4">
            <div>
              <h2 className="text-lg font-bold text-white">
                Patient #{patient.patient_id}
              </h2>
              <p className="text-xs text-slate-400">
                Intelligence Panel {connected ? '· Live' : ''}
              </p>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="p-5 space-y-5">
            <div
              className="rounded-xl p-4"
              style={{ backgroundColor: `${color}15`, border: `1px solid ${color}40` }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">Risk Score</p>
                  <p className="text-3xl font-bold" style={{ color }}>
                    {formatPercent(patient.risk_score)}
                  </p>
                </div>
                <RiskBadge
                  category={
                    patient.risk_score >= 0.6
                      ? 'red'
                      : patient.risk_score >= 0.35
                        ? 'orange'
                        : 'green'
                  }
                  score={patient.risk_score}
                />
              </div>
              <div className="mt-3 flex gap-4 text-sm">
                <span className="text-slate-300">
                  Confidence: <strong>{patient.confidence}</strong>
                </span>
                <span
                  className="font-medium px-2 py-0.5 rounded text-xs"
                  style={{ backgroundColor: `${color}30`, color }}
                >
                  {ALERT_LABELS[level]}
                </span>
              </div>
            </div>

            {patient.vitals && (
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-3">Live Vitals</h3>
                <div className="grid grid-cols-2 gap-2">
                  <Vital icon={<Heart className="h-4 w-4" />} label="Heart Rate" value={`${patient.vitals.hr_mean.toFixed(0)} bpm`} />
                  <Vital icon={<Droplets className="h-4 w-4" />} label="SpO2" value={`${patient.vitals.spo2_mean.toFixed(0)}%`} />
                  <Vital icon={<Thermometer className="h-4 w-4" />} label="Temperature" value={`${patient.vitals.temp_celsius_mean.toFixed(1)}°C`} />
                  <Vital icon={<Wind className="h-4 w-4" />} label="Resp Rate" value={`${patient.vitals.respiratory_rate_mean.toFixed(0)}/min`} />
                  <Vital icon={<Activity className="h-4 w-4" />} label="SBP" value={`${patient.vitals.sbp_mean.toFixed(0)} mmHg`} />
                  {patient.vitals.shock_index != null && (
                    <Vital icon={<Activity className="h-4 w-4" />} label="Shock Index" value={patient.vitals.shock_index.toFixed(2)} />
                  )}
                </div>
              </div>
            )}

            {patient.recommendations.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-2">AI Recommendations</h3>
                <div className="space-y-2">
                  {patient.recommendations.map((r, i) => (
                    <div key={i} className="rounded-lg bg-sky-500/10 border border-sky-500/20 p-3">
                      <p className="text-sm text-sky-300">{r.text}</p>
                      <p className="text-xs text-slate-500 mt-1">{r.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {patient.active_alerts.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-2">Active Alerts</h3>
                {patient.active_alerts.map((a, i) => (
                  <div key={i} className="rounded-lg bg-red-500/10 border border-red-500/20 p-2 mb-2 text-xs">
                    <span className="text-red-400 font-medium">{a.alert_type}</span>
                    <p className="text-slate-400 mt-1">{a.reason}</p>
                  </div>
                ))}
              </div>
            )}

            {patient.deterioration_rate > 0.03 && (
              <div className="rounded-lg bg-orange-500/10 border border-orange-500/20 p-3 text-sm text-orange-400">
                ↑ Deteriorating at {(patient.deterioration_rate * 100).toFixed(1)}% per cycle
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function Vital({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="rounded-lg bg-slate-800/50 p-3">
      <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
        {icon}
        {label}
      </div>
      <p className="font-medium text-white">{value}</p>
    </div>
  )
}
