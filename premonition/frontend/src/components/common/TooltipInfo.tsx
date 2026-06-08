import { HelpCircle } from 'lucide-react'
import { useSettingsStore } from '@/store/settingsStore'

interface TooltipInfoProps {
  text: string
}

export function TooltipInfo({ text }: TooltipInfoProps) {
  const showTooltips = useSettingsStore((s) => s.showTooltips)
  if (!showTooltips) return null

  return (
    <span className="group relative inline-flex">
      <HelpCircle className="h-3.5 w-3.5 cursor-help text-slate-400 hover:text-sky-500" />
      <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-56 -translate-x-1/2 rounded-lg bg-slate-800 px-3 py-2 text-xs text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
        {text}
      </span>
    </span>
  )
}
