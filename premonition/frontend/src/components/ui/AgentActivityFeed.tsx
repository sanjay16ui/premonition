import type { AgentAction } from '@/api/hooks/realtime'

interface AgentActivityFeedProps {
  actions: AgentAction[]
  maxItems?: number
}

const agentColors: Record<string, string> = {
  'Monitoring Agent':  '#06b6d4',
  'Prediction Agent':  '#8b5cf6',
  'Clinical Agent':    '#10b981',
  'Escalation Agent':  '#ef4444',
  'Executive Agent':   '#f59e0b',
}

export function AgentActivityFeed({ actions, maxItems = 20 }: AgentActivityFeedProps) {
  const items = actions.slice(0, maxItems)

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-slate-500">
        Waiting for agent activity...
      </div>
    )
  }

  return (
    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
      {items.map((action, i) => {
        const agentColor = action.explanation
          ? agentColors[action.explanation.agent] || '#94a3b8'
          : '#94a3b8'

        return (
          <div
            key={i}
            className="rounded-xl border border-white/5 p-3 transition-colors hover:bg-white/5"
            style={{ background: 'rgba(15, 23, 42, 0.5)' }}
          >
            <div className="flex items-center justify-between mb-1">
              <span
                className="text-xs font-bold tracking-wide uppercase"
                style={{ color: agentColor }}
              >
                {action.explanation?.agent || 'Agent'}
              </span>
              <span className="text-[10px] text-slate-600">
                Patient {action.patient_id}
              </span>
            </div>

            {action.explanation && (
              <>
                <p className="text-sm text-slate-300 mb-1">
                  <span className="text-slate-500">Reason: </span>
                  {action.explanation.reason}
                </p>
                <p className="text-sm text-slate-300 mb-1">
                  <span className="text-slate-500">Action: </span>
                  {action.explanation.action}
                </p>
                <span
                  className="inline-block rounded-full px-2 py-0.5 text-[10px] font-bold"
                  style={{ background: agentColor + '22', color: agentColor }}
                >
                  Confidence: {action.explanation.confidence}
                </span>
              </>
            )}

            {action.recommendations && action.recommendations.length > 0 && (
              <ul className="mt-2 space-y-0.5 text-xs text-sky-300">
                {action.recommendations.map((rec, j) => (
                  <li key={j}>→ {rec}</li>
                ))}
              </ul>
            )}
          </div>
        )
      })}
    </div>
  )
}
