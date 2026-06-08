import { useState } from 'react'
import { usePredictionHistory } from '@/api/hooks'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { LoadingOverlay } from '@/components/common/LoadingOverlay'
import { EmptyState } from '@/components/ui/EmptyState'
import { PredictionTimelineChart } from '@/components/charts/PredictionTimelineChart'
import { formatTimestamp, formatPercent } from '@/utils/format'
import { predictionLabelFriendly } from '@/utils/risk'

export function PredictionHistoryPage() {
  const [limit, setLimit] = useState(50)
  const { data, isLoading } = usePredictionHistory({ limit })

  if (isLoading) return <LoadingOverlay label="Loading prediction history..." />

  const items = data?.items || []

  const timeline = buildTimeline(items)

  return (
    <PageContainer
      title="Prediction History"
      subtitle="Complete log of all sepsis risk assessments"
    >
      <div className="mb-4 flex items-center gap-3">
        <label className="text-sm text-slate-500">Show</label>
        <select
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-sm"
        >
          <option value={25}>25</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
        <span className="text-sm text-slate-400">records</span>
      </div>

      {items.length === 0 ? (
        <EmptyState
          title="No predictions recorded"
          description="Predictions will appear here automatically after you run risk assessments."
        />
      ) : (
        <>
          <GlassCard className="mb-6" title="Activity Timeline">
            <PredictionTimelineChart data={timeline} />
          </GlassCard>

          <GlassCard title={`${data?.count || 0} Predictions`}>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 text-left text-xs text-slate-400">
                    <th className="pb-3 pr-4">Time</th>
                    <th className="pb-3 pr-4">Patient</th>
                    <th className="pb-3 pr-4">Risk</th>
                    <th className="pb-3 pr-4">Status</th>
                    <th className="pb-3 pr-4">Confidence</th>
                    <th className="pb-3">Summary</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((p, i) => (
                    <tr
                      key={`${p.patient_id}-${p.timestamp}-${i}`}
                      className="border-b border-slate-100 dark:border-slate-800"
                    >
                      <td className="py-3 pr-4 text-xs text-slate-400 whitespace-nowrap">
                        {formatTimestamp(p.timestamp)}
                      </td>
                      <td className="py-3 pr-4 font-medium">#{p.patient_id}</td>
                      <td className="py-3 pr-4">{formatPercent(p.risk_score)}</td>
                      <td className="py-3 pr-4">
                        <RiskBadge
                          category={
                            p.risk_score >= 0.6 ? 'red' : p.risk_score >= 0.35 ? 'orange' : 'green'
                          }
                        />
                      </td>
                      <td className="py-3 pr-4">{p.confidence}</td>
                      <td className="py-3 text-xs text-slate-400 max-w-xs truncate">
                        {p.explanation_summary || predictionLabelFriendly(p.prediction_label)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}
    </PageContainer>
  )
}

function buildTimeline(
  items: { timestamp: string; prediction_label: string }[],
) {
  const buckets = new Map<string, { alerts: number; total: number }>()
  for (const item of items) {
    const d = new Date(item.timestamp)
    const key = `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
    const b = buckets.get(key) || { alerts: 0, total: 0 }
    b.total++
    if (item.prediction_label === 'sepsis_alert') b.alerts++
    buckets.set(key, b)
  }
  return Array.from(buckets.entries()).map(([time, v]) => ({ time, ...v }))
}
