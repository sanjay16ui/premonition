import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Kpi { label: string; value: string; change: number; unit?: string }

interface Props { kpis: Kpi[] }

export function ExecutiveKpiDashboard({ kpis }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {kpis.map((kpi, i) => (
        <motion.div
          key={kpi.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="rounded-2xl border border-slate-200/50 dark:border-slate-700/50 bg-white/60 dark:bg-slate-800/60 p-5 backdrop-blur"
        >
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{kpi.label}</p>
          <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {kpi.value}{kpi.unit && <span className="text-lg text-slate-400">{kpi.unit}</span>}
          </p>
          <div className="mt-2 flex items-center gap-1 text-sm">
            {kpi.change > 0 ? <TrendingUp className="h-4 w-4 text-emerald-500" /> :
             kpi.change < 0 ? <TrendingDown className="h-4 w-4 text-red-500" /> :
             <Minus className="h-4 w-4 text-slate-400" />}
            <span className={kpi.change > 0 ? 'text-emerald-500' : kpi.change < 0 ? 'text-red-500' : 'text-slate-400'}>
              {kpi.change > 0 ? '+' : ''}{kpi.change}%
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  )
}
