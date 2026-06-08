import { useHealth, useMetrics, useSystemStatus } from '@/api/hooks'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { StatCard } from '@/components/ui/StatCard'
import { LoadingOverlay } from '@/components/common/LoadingOverlay'
import { ErrorState } from '@/components/ui/ErrorState'
import { SystemMetricsChart } from '@/components/charts/SystemMetricsChart'
import { formatUptime } from '@/utils/format'

export function SystemHealthPage() {
  const { data: health, isLoading: hLoading } = useHealth()
  const { data: status, isLoading: sLoading, error, refetch } = useSystemStatus()
  const { data: metrics } = useMetrics()

  if (hLoading || sLoading) return <LoadingOverlay label="Checking system health..." />
  if (error) return <ErrorState message={String(error)} onRetry={() => refetch()} />

  const chartData = metrics
    ? [
        {
          label: 'Current',
          predictions: metrics.predictions_total,
          alerts: metrics.predictions_sepsis_alerts,
          errors: metrics.predictions_errors,
        },
      ]
    : []

  return (
    <PageContainer
      title="System Health Dashboard"
      subtitle="API, model, and infrastructure status"
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="API Status"
          value={health?.status === 'ok' ? 'Healthy' : 'Down'}
          color={health?.status === 'ok' ? '#10b981' : '#ef4444'}
          tooltip="FastAPI liveness probe response"
        />
        <StatCard
          label="Model Loaded"
          value={status?.model_loaded ? 'Yes' : 'No'}
          color={status?.model_loaded ? '#10b981' : '#ef4444'}
          tooltip="Whether ML model artifacts are loaded in memory"
        />
        <StatCard
          label="Uptime"
          value={formatUptime(status?.uptime_seconds || metrics?.uptime_seconds || 0)}
          tooltip="Server uptime since last restart"
        />
        <StatCard
          label="Avg Latency"
          value={`${(metrics?.avg_latency_ms || 0).toFixed(0)}ms`}
          tooltip="Average prediction response time"
          color="#0ea5e9"
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <GlassCard title="Service Details">
          <div className="space-y-3 text-sm">
            <Row label="Service" value={health?.service || '—'} />
            <Row label="API Version" value={health?.version || '—'} />
            <Row label="System Status" value={status?.status || '—'} />
            <Row label="Model" value={status?.model_name || 'Not loaded'} />
            <Row label="Model Version" value={status?.model_version || '—'} />
            <Row label="Feature Tier" value={status?.tier || '—'} />
            <Row label="Predictions Served" value={String(status?.predictions_served || 0)} />
            <Row label="Last Prediction" value={status?.last_prediction_at || 'Never'} />
          </div>
        </GlassCard>

        <GlassCard title="Operational Metrics">
          <SystemMetricsChart data={chartData} />
          <div className="mt-4 grid grid-cols-3 gap-3 text-center text-sm">
            <div className="rounded-xl bg-sky-500/10 p-3">
              <p className="text-xs text-slate-400">Total</p>
              <p className="font-bold text-sky-500">{metrics?.predictions_total || 0}</p>
            </div>
            <div className="rounded-xl bg-red-500/10 p-3">
              <p className="text-xs text-slate-400">Alerts</p>
              <p className="font-bold text-red-500">{metrics?.predictions_sepsis_alerts || 0}</p>
            </div>
            <div className="rounded-xl bg-amber-500/10 p-3">
              <p className="text-xs text-slate-400">Errors</p>
              <p className="font-bold text-amber-500">{metrics?.predictions_errors || 0}</p>
            </div>
          </div>
        </GlassCard>
      </div>
    </PageContainer>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium text-right max-w-[60%] truncate">{value}</span>
    </div>
  )
}
