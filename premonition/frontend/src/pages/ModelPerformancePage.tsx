import { useModelVersion } from '@/api/hooks'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { StatCard } from '@/components/ui/StatCard'
import { LoadingOverlay } from '@/components/common/LoadingOverlay'
import { ErrorState } from '@/components/ui/ErrorState'
import { ModelPerformanceChart } from '@/components/charts/ModelPerformanceChart'
import { ScreenshotPlaceholder } from '@/components/ui/ScreenshotPlaceholder'
import { formatPercent } from '@/utils/format'

interface MetricBlock {
  model_name?: string
  pr_auc?: number
  recall?: number
  f1?: number
  roc_auc?: number
  accuracy?: number
  precision?: number
}

export function ModelPerformancePage() {
  const { data: model, isLoading, error, refetch } = useModelVersion()

  if (isLoading) return <LoadingOverlay label="Loading model metrics..." />
  if (error) return <ErrorState message={String(error)} onRetry={() => refetch()} />

  const metrics = model?.metrics as {
    test?: MetricBlock
    validation?: MetricBlock
    selection?: { comparison?: MetricBlock[] }
  }
  const test = metrics?.test
  const comparison = metrics?.selection?.comparison || []

  const chartData = comparison.map((m) => ({
    model: (m.model_name || 'unknown').replace('_', ' '),
    pr_auc: m.pr_auc || 0,
    recall: m.recall || 0,
    f1: m.f1 || 0,
    roc_auc: m.roc_auc || 0,
  }))

  return (
    <PageContainer
      title="Model Performance Dashboard"
      subtitle="How accurately PREMONITION detects sepsis"
    >
      <GlassCard className="mb-6">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          These metrics measure how well the AI identifies sepsis on patients it has never seen before.
          <strong> PR-AUC</strong> is the primary metric — it balances catching true cases vs. false alarms.
          <strong> Recall</strong> measures how many actual sepsis cases we catch (higher = fewer missed cases).
        </p>
      </GlassCard>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="PR-AUC (Test)"
          value={test?.pr_auc ? formatPercent(test.pr_auc) : '—'}
          tooltip="Precision-Recall Area Under Curve — primary selection metric"
          color="#8b5cf6"
        />
        <StatCard
          label="Recall (Test)"
          value={test?.recall ? formatPercent(test.recall) : '—'}
          tooltip="% of actual sepsis cases correctly identified"
          color="#10b981"
        />
        <StatCard
          label="ROC-AUC (Test)"
          value={test?.roc_auc ? formatPercent(test.roc_auc) : '—'}
          tooltip="Overall discrimination ability"
          color="#0ea5e9"
        />
        <StatCard
          label="F1 Score (Test)"
          value={test?.f1 ? test.f1.toFixed(3) : '—'}
          tooltip="Harmonic mean of precision and recall"
          color="#f59e0b"
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <GlassCard title="Model Comparison" subtitle="All trained models on validation set">
          <ModelPerformanceChart data={chartData} />
        </GlassCard>

        <GlassCard title="Active Model" subtitle={`${model?.model_name} v${model?.model_version}`}>
          <div className="space-y-3 text-sm">
            <Row label="Tier" value={model?.tier || '—'} />
            <Row label="Features" value={String(model?.n_features || 0)} />
            <Row label="Trained" value={model?.training_timestamp || '—'} />
            <Row label="Dataset Hash" value={model?.dataset_hash?.slice(0, 12) + '...' || '—'} />
            <Row label="Accuracy" value={test?.accuracy ? formatPercent(test.accuracy) : '—'} />
            <Row label="Precision" value={test?.precision ? formatPercent(test.precision) : '—'} />
          </div>
        </GlassCard>
      </div>

      <GlassCard className="mt-6" title="Confusion Matrix Preview" subtitle="Test set classification results">
        <ScreenshotPlaceholder
          label="Confusion Matrix Heatmap"
          description="Run scripts/explain.py to generate full evaluation plots in reports/"
        />
      </GlassCard>
    </PageContainer>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}
