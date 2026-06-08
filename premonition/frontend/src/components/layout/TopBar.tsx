import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Menu, HeartPulse, ChevronRight, ArrowLeft } from 'lucide-react'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import { useSystemStatus } from '@/api/hooks'
import { ROUTES } from '@/routes/paths'

interface TopBarProps {
  onMenuClick?: () => void
}

function Breadcrumbs() {
  const location = useLocation()
  const navigate = useNavigate()
  const pathnames = location.pathname.split('/').filter((x) => x)

  return (
    <div className="hidden lg:flex items-center gap-2 text-sm text-slate-500 font-medium">
      <button onClick={() => navigate(-1)} className="mr-2 hover:text-slate-300 transition-colors">
        <ArrowLeft className="h-4 w-4" />
      </button>
      <Link to="/" className="hover:text-slate-300 transition-colors">Home</Link>
      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`
        const isLast = index === pathnames.length - 1
        return (
          <div key={to} className="flex items-center gap-2">
            <ChevronRight className="h-4 w-4 text-slate-700" />
            {isLast ? (
              <span className="text-slate-200 capitalize">{value.replace('-', ' ')}</span>
            ) : (
              <Link to={to} className="hover:text-slate-300 capitalize transition-colors">
                {value.replace('-', ' ')}
              </Link>
            )}
          </div>
        )
      })}
    </div>
  )
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const { data: status } = useSystemStatus()
  const isDemoMode = localStorage.getItem('premonition_demo_mode') === 'true'

  return (
    <>
      {/* Demo Mode Banner */}
      {isDemoMode && (
        <div className="sticky top-0 z-50 flex items-center justify-center gap-2 bg-amber-500/20 border-b border-amber-500/30 py-1 px-4 text-xs text-amber-400 font-semibold tracking-wide">
          <span>⚡</span>
          <span>DEMO MODE ACTIVE — Instant access via demo account.</span>
          <button
            onClick={() => {
              localStorage.removeItem('premonition_demo_mode')
              window.location.reload()
            }}
            className="ml-4 underline hover:text-amber-300 transition-colors text-xs font-normal"
          >
            Exit Demo
          </button>
        </div>
      )}

      <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-slate-800/60 bg-slate-900/80 backdrop-blur-md px-4 lg:px-6 shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
          >
            <Menu className="h-4 w-4" />
          </button>
          <Link to={ROUTES.landing} className="flex items-center gap-2 lg:hidden">
            <HeartPulse className="h-5 w-5 text-indigo-500" />
            <span className="font-bold text-slate-100 tracking-wide">PREMONITION</span>
          </Link>
          <Breadcrumbs />
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-2 sm:flex bg-slate-800/50 px-3 py-1.5 rounded-md border border-slate-700/50">
            <span
              className={`h-2 w-2 rounded-full ${
                status?.model_loaded
                  ? 'bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-xs font-semibold text-slate-300 tracking-wide uppercase">
              {status?.status === 'ready' ? 'System Ready' : 'System Degraded'}
            </span>
          </div>
          <ThemeToggle />
        </div>
      </header>
    </>
  )
}
