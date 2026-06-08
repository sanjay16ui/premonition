import { Html } from '@react-three/drei'
import { trafficLight, riskToLevel, humanRiskLabel } from '@/theme/colors'
import type { PatientMonitorState } from '@/api/types'
import type { AgentAction } from '@/api/hooks/realtime'
import { Brain, HeartPulse, Activity } from 'lucide-react'

interface Props {
  patient: PatientMonitorState
  recentActions: AgentAction[]
  onClose: () => void
}

export function PatientIntelligenceHUD({ patient, recentActions, onClose }: Props) {
  const level = riskToLevel(patient.risk_score)
  const tl = trafficLight[level]
  const label = humanRiskLabel(patient.risk_score)

  const patientActions = recentActions.filter(a => a.patient_id === patient.patient_id).slice(0, 3)

  return (
    <Html
      position={[0, 2, 0]}
      center
      zIndexRange={[100, 0]}
      style={{
        pointerEvents: 'auto',
      }}
    >
      <div 
        className="w-80 rounded-2xl border p-4 shadow-2xl backdrop-blur-xl"
        style={{
          background: 'rgba(15, 23, 42, 0.85)',
          borderColor: `rgba(255,255,255,0.1)`,
          boxShadow: `0 0 40px ${tl.glow}, inset 0 0 20px ${tl.glow}`,
        }}
      >
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="text-lg font-bold text-white">Patient #{patient.patient_id}</h3>
            <p className="text-xs font-mono" style={{ color: tl.text }}>
              {tl.emoji} {label.title}
            </p>
          </div>
          <button 
            onClick={(e) => { e.stopPropagation(); onClose() }}
            className="rounded-full bg-white/10 p-1 hover:bg-white/20 text-slate-300"
          >
            ✕
          </button>
        </div>

        <div className="mb-4 grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-black/40 p-2 text-center border border-white/5">
            <p className="text-[10px] text-slate-400 uppercase tracking-widest flex items-center justify-center gap-1">
              <HeartPulse className="w-3 h-3 text-red-400" /> HR
            </p>
            <p className="text-xl font-mono text-white">{Math.round(patient.vitals?.hr_mean || 0)}</p>
          </div>
          <div className="rounded-lg bg-black/40 p-2 text-center border border-white/5">
            <p className="text-[10px] text-slate-400 uppercase tracking-widest flex items-center justify-center gap-1">
              <Activity className="w-3 h-3 text-sky-400" /> MAP
            </p>
            <p className="text-xl font-mono text-white">
              {patient.vitals ? Math.round((patient.vitals.sbp_mean + 2 * patient.vitals.dbp_mean) / 3) : 0}
            </p>
          </div>
        </div>

        <div className="mb-4">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
            <Brain className="w-3 h-3 text-violet-400" /> SHAP Reasoning
          </h4>
          <div className="space-y-1">
            {patient.recommendations?.slice(0,2).map((rec, i) => (
              <p key={i} className="text-xs text-slate-300 bg-white/5 rounded px-2 py-1">
                {rec.text}
              </p>
            )) || <p className="text-xs text-slate-500">No recent insights.</p>}
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
            Agentic Activity
          </h4>
          {patientActions.length > 0 ? (
            <div className="space-y-2">
              {patientActions.map((action, i) => (
                <div key={i} className="text-xs bg-black/30 rounded border border-white/5 p-2">
                  <span className="font-bold text-emerald-400">{action.explanation?.agent || 'Agent'}: </span>
                  <span className="text-slate-300">{action.explanation?.action}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[10px] text-slate-500 italic">No autonomous actions pending.</p>
          )}
        </div>
      </div>
    </Html>
  )
}
