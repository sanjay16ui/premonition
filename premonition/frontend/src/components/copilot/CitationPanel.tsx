import { FileText, X } from 'lucide-react'
import type { CopilotCitation } from '@/api/copilotTypes'

interface CitationPanelProps {
  citation: CopilotCitation | null
  onClose: () => void
}

export function CitationPanel({ citation, onClose }: CitationPanelProps) {
  if (!citation) return null

  return (
    <div className="border-l border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-indigo-400" />
          <h3 className="text-sm font-semibold">Source</h3>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
          <X className="h-4 w-4" />
        </button>
      </div>
      <p className="mb-1 text-sm font-medium">{citation.title}</p>
      <p className="mb-2 text-xs text-slate-400">Score: {(citation.score * 100).toFixed(1)}%</p>
      <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">{citation.excerpt}</p>
      <p className="mt-2 text-xs text-slate-400">ID: {citation.source_id}</p>
    </div>
  )
}
