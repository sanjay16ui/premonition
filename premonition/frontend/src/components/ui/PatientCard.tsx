import { trafficLight, humanRiskLabel, riskToLevel } from '@/theme/colors'
import type { AlertLevel } from '@/theme/colors'

interface PatientCardProps {
  patientId: string
  name?: string
  age?: number
  room?: string
  riskScore: number
  alertLevel?: string
  trend?: 'rising' | 'falling' | 'stable'
  nextAction?: string
  onClick?: () => void
}

const trendArrow: Record<string, { symbol: string; color: string; label: string }> = {
  rising:  { symbol: '↑', color: '#ef4444', label: 'worsening' },
  falling: { symbol: '↓', color: '#10b981', label: 'improving' },
  stable:  { symbol: '→', color: '#94a3b8', label: 'stable' },
}

export function PatientCard({
  patientId,
  name,
  age,
  room,
  riskScore,
  alertLevel,
  trend = 'stable',
  nextAction,
  onClick,
}: PatientCardProps) {
  const level = (alertLevel?.toUpperCase() as AlertLevel) || riskToLevel(riskScore)
  const tl = trafficLight[level] || trafficLight.GREEN
  const label = humanRiskLabel(riskScore)
  const t = trendArrow[trend] || trendArrow.stable

  return (
    <button
      onClick={onClick}
      className="w-full text-left rounded-2xl border border-white/10 p-5 transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl focus:outline-none focus:ring-2 focus:ring-sky-500/50"
      style={{
        background: 'rgba(15, 23, 42, 0.7)',
        backdropFilter: 'blur(16px) saturate(180%)',
        boxShadow: `0 0 20px ${tl.glow}, 0 4px 20px rgba(0,0,0,0.3)`,
      }}
    >
      {/* Status bar */}
      <div
        className="mb-3 flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-bold tracking-wider uppercase"
        style={{ background: tl.bg, color: tl.text }}
      >
        <span className="text-base">{tl.emoji}</span>
        <span>{label.title}</span>
      </div>

      {/* Patient info */}
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-lg font-semibold text-white truncate">
          {name || `Patient ${patientId}`}
        </h3>
        {age && <span className="text-xs text-slate-400">Age {age}</span>}
      </div>
      {room && <p className="text-xs text-slate-500 mb-3">Room {room}</p>}

      {/* Risk display */}
      <div className="flex items-end justify-between mb-3">
        <div>
          <p className="text-3xl font-black text-white">
            {Math.round(riskScore * 100)}%
          </p>
          <p className="text-xs text-slate-400">{label.subtitle}</p>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-2xl" style={{ color: t.color }}>{t.symbol}</span>
          <span className="text-[10px] text-slate-500">{t.label}</span>
        </div>
      </div>

      {/* Next action */}
      {nextAction && (
        <div className="rounded-xl bg-white/5 px-3 py-2 text-xs text-slate-300 border border-white/5">
          <span className="font-medium text-sky-400">Action: </span>
          {nextAction}
        </div>
      )}
    </button>
  )
}
