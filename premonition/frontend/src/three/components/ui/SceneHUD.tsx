import { Link } from 'react-router-dom'
import { Radio, Box, LayoutDashboard } from 'lucide-react'
import { ROUTES } from '@/routes/paths'
import type { ExecutiveSummary } from '@/api/types'

interface SceneHUDProps {
  title: string
  subtitle?: string
  connected: boolean
  executive?: ExecutiveSummary | null
  patientCount?: number
}

export function SceneHUD({
  title,
  subtitle,
  connected,
  executive,
  patientCount,
}: SceneHUDProps) {
  return (
    <div className="pointer-events-none absolute inset-0 z-40 flex flex-col">
      <div className="pointer-events-auto flex items-center justify-between px-6 py-4">
        <div>
          <h1 className="text-xl font-bold gradient-text">{title}</h1>
          {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs ${
              connected
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-slate-700/50 text-slate-400'
            }`}
          >
            <Radio className={`h-3 w-3 ${connected ? 'animate-pulse' : ''}`} />
            {connected ? 'Live Stream' : 'Offline'}
          </span>
          <nav className="flex gap-2">
            <NavLink to={ROUTES.digitalTwin} icon={<Box className="h-3.5 w-3.5" />} label="Twin" />
            <NavLink to={ROUTES.executive3d} icon={<LayoutDashboard className="h-3.5 w-3.5" />} label="Executive" />
          </nav>
        </div>
      </div>

      {executive && (
        <div className="pointer-events-auto mx-6 mt-auto mb-4 flex gap-3">
          <StatPill label="Patients" value={String(executive.current_icu_patients)} />
          <StatPill label="High Risk" value={String(executive.high_risk_count)} color="#f97316" />
          <StatPill label="Critical" value={String(executive.critical_alert_count)} color="#ef4444" />
          <StatPill label="Alerts" value={String(executive.alerts_today)} color="#f59e0b" />
          {patientCount !== undefined && (
            <StatPill label="Beds" value={String(patientCount)} color="#38bdf8" />
          )}
        </div>
      )}

      <p className="pointer-events-none absolute bottom-4 right-6 text-[10px] text-slate-600">
        Click a bed to open patient intelligence · Drag to orbit · Scroll to zoom
      </p>
    </div>
  )
}

function NavLink({
  to,
  icon,
  label,
}: {
  to: string
  icon: React.ReactNode
  label: string
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-1.5 rounded-lg bg-slate-800/80 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 hover:text-white backdrop-blur"
    >
      {icon}
      {label}
    </Link>
  )
}

function StatPill({
  label,
  value,
  color = '#38bdf8',
}: {
  label: string
  value: string
  color?: string
}) {
  return (
    <div className="glass rounded-xl px-4 py-2 backdrop-blur">
      <p className="text-[10px] text-slate-400">{label}</p>
      <p className="text-lg font-bold" style={{ color }}>
        {value}
      </p>
    </div>
  )
}
