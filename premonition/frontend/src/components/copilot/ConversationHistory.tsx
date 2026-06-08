import { MessageSquare } from 'lucide-react'
import type { ConversationSummary } from '@/api/copilotTypes'

interface ConversationHistoryProps {
  conversations: ConversationSummary[]
  activeId?: string
  onSelect: (id: string) => void
}

export function ConversationHistory({ conversations, activeId, onSelect }: ConversationHistoryProps) {
  if (conversations.length === 0) {
    return <p className="p-4 text-xs text-slate-400">No conversations yet</p>
  }

  return (
    <div className="space-y-1 p-2">
      {conversations.map((conv) => (
        <button
          key={conv.id}
          onClick={() => onSelect(conv.id)}
          className={`flex w-full items-start gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
            activeId === conv.id
              ? 'bg-indigo-500/10 text-indigo-400'
              : 'hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <MessageSquare className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="min-w-0">
            <p className="truncate font-medium">{conv.title}</p>
            <p className="text-xs text-slate-400">{conv.message_count} messages</p>
          </div>
        </button>
      ))}
    </div>
  )
}
