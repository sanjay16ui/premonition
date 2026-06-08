import { useState } from 'react'
import { useAuditLogs } from '@/api/hooks'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { LoadingOverlay } from '@/components/common/LoadingOverlay'
import { EmptyState } from '@/components/ui/EmptyState'
import { formatTimestamp, formatPercent } from '@/utils/format'

export function AuditLogPage() {
  const [filter, setFilter] = useState<string>('')
  const { data, isLoading } = useAuditLogs({
    limit: 100,
    prediction_label: filter || undefined,
  })

  if (isLoading) return <LoadingOverlay label="Loading audit logs..." />

  const items = data?.items || []

  return (
    <PageContainer
      title="Audit Log Dashboard"
      subtitle="Full compliance trail — every prediction with explanation details"
    >
      <GlassCard className="mb-6">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Audit logs record every AI prediction for regulatory compliance and clinical review.
          Each entry includes the risk score, model version, explanation, and top contributing factors.
        </p>
      </GlassCard>

      <div className="mb-4 flex gap-2">
        {['', 'sepsis_alert', 'no_alert'].map((f) => (
          <button
            key={f || 'all'}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              filter === f
                ? 'bg-sky-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800'
            }`}
          >
            {f === '' ? 'All' : f === 'sepsis_alert' ? 'Alerts' : 'No Alert'}
          </button>
        ))}
      </div>

      {items.length === 0 ? (
        <EmptyState
          title="No audit records"
          description="Audit entries are created automatically when predictions are made."
        />
      ) : (
        <div className="space-y-4">
          {items.map((log, i) => (
            <GlassCard key={`${log.patient_id}-${log.timestamp}-${i}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-bold">Patient #{log.patient_id}</p>
                  <p className="text-xs text-slate-400">
                    {formatTimestamp(log.timestamp)} · {log.model_name} v{log.model_version}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{formatPercent(log.risk_score)}</span>
                  <RiskBadge
                    category={
                      log.risk_score >= 0.6 ? 'red' : log.risk_score >= 0.35 ? 'orange' : 'green'
                    }
                  />
                </div>
              </div>
              <p className="mt-3 text-sm">{log.explanation_summary}</p>
              {log.top_factors.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {log.top_factors.map((f) => (
                    <span
                      key={f}
                      className="rounded-full bg-violet-500/10 px-2.5 py-0.5 text-xs text-violet-500"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              )}
              {log.request_id && (
                <p className="mt-2 text-[10px] text-slate-400">
                  Request ID: {log.request_id}
                </p>
              )}
            </GlassCard>
          ))}
        </div>
      )}
    </PageContainer>
  )
}
