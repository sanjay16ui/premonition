import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileSearch,
  HeartPulse,
  Box,
  Settings,
  Bot,
  Bell,
  BarChart3,
  MonitorPlay,
  ActivitySquare
} from 'lucide-react'
import { ROUTES } from '@/routes/paths'

const navItems = [
  { to: ROUTES.landing, label: 'Overview', icon: BarChart3, end: true },
  { to: ROUTES.liveMonitoring, label: 'Live Patients', icon: MonitorPlay },
  { to: ROUTES.analyticsDashboard, label: 'Analytics', icon: ActivitySquare },
  { to: ROUTES.copilot, label: 'AI Copilot', icon: Bot },
  { to: ROUTES.digitalTwin, label: 'Digital Twin', icon: Box },
  { to: ROUTES.executive3d, label: 'Executive 3D', icon: Bell },
  { to: ROUTES.settings, label: 'Settings', icon: Settings },
]

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-950 lg:flex shadow-2xl z-50">
      <div className="flex h-16 items-center gap-3 border-b border-slate-800/60 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 shadow-[0_0_15px_rgba(79,70,229,0.5)]">
          <HeartPulse className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold tracking-widest text-slate-100 uppercase">Premonition</p>
          <p className="text-[10px] text-indigo-400 font-medium tracking-wide">Agentic AI Platform</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1.5 p-4 overflow-y-auto">
        <div className="mb-4 px-2 text-[10px] font-semibold tracking-widest text-slate-500 uppercase">Main Menu</div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`h-4 w-4 transition-colors duration-200 ${isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                {item.label}
                {isActive && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.8)]"
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-800/60 p-4">
        <div className="rounded-lg bg-slate-900 border border-slate-800 p-3 shadow-inner">
          <div className="flex items-center gap-2">
            <FileSearch className="h-4 w-4 text-emerald-500" />
            <p className="text-xs font-semibold text-slate-200 tracking-wide">
              System Active
            </p>
          </div>
          <p className="mt-1.5 text-[10px] text-slate-400 leading-relaxed">
            Realtime AI prediction pipeline is monitoring all streams.
          </p>
        </div>
      </div>
    </aside>
  )
}
