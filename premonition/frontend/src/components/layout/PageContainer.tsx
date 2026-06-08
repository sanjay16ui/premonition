import type { ReactNode } from 'react'
import { motion } from 'framer-motion'

interface PageContainerProps {
  title: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
}

export function PageContainer({
  title,
  subtitle,
  action,
  children,
}: PageContainerProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6">
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {subtitle}
            </p>
          )}
        </div>
        {action}
      </motion.div>
      {children}
    </div>
  )
}
