import { Image } from 'lucide-react'

interface ScreenshotPlaceholderProps {
  label: string
  description?: string
}

export function ScreenshotPlaceholder({
  label,
  description,
}: ScreenshotPlaceholderProps) {
  return (
    <div className="flex aspect-video flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50">
      <Image className="mb-2 h-8 w-8 text-slate-400" />
      <p className="text-sm font-medium text-slate-500">{label}</p>
      {description && (
        <p className="mt-1 max-w-xs text-center text-xs text-slate-400">
          {description}
        </p>
      )}
    </div>
  )
}
