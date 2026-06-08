import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { TooltipInfo } from '@/components/common/TooltipInfo'

interface StatCardProps {
  label: string
  value: string | number
  icon?: ReactNode
  trend?: string
  tooltip?: string
  color?: string
  delay?: number
}

export function StatCard({
  label,
  value,
  icon,
  trend,
  tooltip,
  color = '#0ea5e9',
  delay = 0,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, delay }}
      className="glass rounded-2xl p-4"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-1.5">
            <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
            {tooltip && <TooltipInfo text={tooltip} />}
          </div>
          <p className="mt-1 text-2xl font-bold" style={{ color }}>
            {value}
          </p>
          {trend && (
            <p className="mt-1 text-xs text-slate-400">{trend}</p>
          )}
        </div>
        {icon && (
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl"
            style={{ backgroundColor: `${color}15`, color }}
          >
            {icon}
          </div>
        )}
      </div>
    </motion.div>
  )
}
