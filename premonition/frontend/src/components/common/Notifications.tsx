import { AnimatePresence, motion } from 'framer-motion'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import {
  useNotificationStore,
  type NotificationType,
} from '@/store/notificationStore'

const icons: Record<NotificationType, typeof Info> = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
}

const colors: Record<NotificationType, string> = {
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  error: 'border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400',
  info: 'border-sky-500/30 bg-sky-500/10 text-sky-600 dark:text-sky-400',
  warning: 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400',
}

export function Notifications() {
  const { items, remove } = useNotificationStore()

  return (
    <div className="fixed right-4 top-4 z-[100] flex w-96 max-w-[calc(100vw-2rem)] flex-col gap-2">
      <AnimatePresence>
        {items.map((n) => {
          const Icon = icons[n.type]
          return (
            <motion.div
              key={n.id}
              initial={{ opacity: 0, x: 80 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 80 }}
              className={`glass-strong flex items-start gap-3 rounded-xl border p-4 shadow-xl ${colors[n.type]}`}
            >
              <Icon className="mt-0.5 h-5 w-5 shrink-0" />
              <div className="flex-1">
                <p className="font-medium text-slate-800 dark:text-slate-100">
                  {n.title}
                </p>
                {n.message && (
                  <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
                    {n.message}
                  </p>
                )}
              </div>
              <button
                onClick={() => remove(n.id)}
                className="shrink-0 text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
