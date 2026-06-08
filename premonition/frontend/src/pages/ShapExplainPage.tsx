import { useState } from 'react'
import { Brain, Play } from 'lucide-react'
import { useExplain } from '@/api/hooks'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { ShapContributionChart } from '@/components/charts/ShapContributionChart'
import { FeatureImportanceChart } from '@/components/charts/FeatureImportanceChart'
import { SAMPLE_PATIENT, SAMPLE_PATIENT_LOW_RISK, SAMPLE_PATIENT_C } from '@/data/samplePatient'
import { useNotificationStore } from '@/store/notificationStore'
import { useSettingsStore } from '@/store/settingsStore'
import type { PatientFeatures } from '@/api/types'

export function ShapExplainPage() {
  const [patientId, setPatientId] = useState('37464')
  const explain = useExplain()
  const notify = useNotificationStore()
  const topN = useSettingsStore((s) => s.defaultTopN)

  const getPatientFeatures = (id: string): PatientFeatures => {
    if (id === '34024') return SAMPLE_PATIENT_LOW_RISK
    if (id === '30010') return SAMPLE_PATIENT_C
    return SAMPLE_PATIENT
  }

  const handleExplain = async () => {
    try {
      await explain.mutateAsync({
        patient_id: patientId,
        features: getPatientFeatures(patientId),
        top_n: topN,
      })
      notify.success('Explanation generated')
    } catch (err) {
      notify.error('Explanation failed', err instanceof Error ? err.message : 'Unknown error')
    }
  }

  const result = explain.data
  const shapData =
    result?.top_factors.map((f) => ({
      feature: f.feature,
      value: f.shap_value || 0,
    })) || []
  const factorData =
    result?.top_factors.map((f) => ({
      feature: f.feature,
      contribution: f.contribution_pct,
      direction: f.direction,
    })) || []

  return (
    <PageContainer
      title="SHAP Explainability"
      subtitle="Understand exactly why the AI flagged this patient"
      action={
        <Button
          loading={explain.isPending}
          icon={<Play className="h-4 w-4" />}
          onClick={handleExplain}
        >
          Generate Explanation
        </Button>
      }
    >
      <GlassCard className="mb-6">
        <div className="flex items-start gap-4">
          <Brain className="h-10 w-10 text-violet-500 shrink-0" />
          <div>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              <strong>SHAP</strong> (SHapley Additive exPlanations) breaks down the AI's
              decision into contributions from each measurement. Think of it as a receipt
              showing what pushed the risk score up (red) or down (green).
            </p>
            <p className="mt-2 text-xs text-slate-400">
              This makes the AI transparent and auditable — critical for clinical trust.
            </p>
          </div>
        </div>
      </GlassCard>

      <div className="mb-6 space-y-4">
        <div>
          <label className="text-sm text-slate-500">Patient ID</label>
          <input
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="mt-1 block w-48 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2 text-sm"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            onClick={() => setPatientId('37464')}
          >
            Patient A (High-Risk)
          </Button>
          <Button
            variant="secondary"
            onClick={() => setPatientId('34024')}
          >
            Patient B (Low-Risk)
          </Button>
          <Button
            variant="secondary"
            onClick={() => setPatientId('30010')}
          >
            Patient C (Medium-Risk)
          </Button>
        </div>
      </div>

      {result ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <GlassCard title="Explanation Summary">
            <div className="mb-4 flex items-center gap-3">
              <p className="text-lg font-bold">Patient #{result.patient_id}</p>
              <RiskBadge category={result.risk_category} score={result.risk_score} />
            </div>
            <p className="text-sm leading-relaxed">{result.explanation_summary}</p>

            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-xl bg-red-500/10 p-3">
                <p className="text-xs text-red-400 mb-1">Risk Increasers</p>
                {result.shap.risk_increasers.map((f) => (
                  <p key={f} className="text-xs">↑ {f}</p>
                ))}
              </div>
              <div className="rounded-xl bg-emerald-500/10 p-3">
                <p className="text-xs text-emerald-400 mb-1">Risk Decreasers</p>
                {result.shap.risk_decreasers.map((f) => (
                  <p key={f} className="text-xs">↓ {f}</p>
                ))}
              </div>
            </div>

            {result.shap.dominant_category && (
              <p className="mt-3 text-xs text-slate-400">
                Dominant clinical category: <strong>{result.shap.dominant_category}</strong>
              </p>
            )}
          </GlassCard>

          <GlassCard title="SHAP Contribution Values">
            <ShapContributionChart
              data={shapData}
              baseValue={result.shap.base_value}
            />
          </GlassCard>

          <GlassCard className="lg:col-span-2" title="Feature Importance (%)">
            <FeatureImportanceChart data={factorData} />
          </GlassCard>
        </div>
      ) : (
        <GlassCard>
          <p className="py-12 text-center text-sm text-slate-400">
            Click "Generate Explanation" to see why the AI assessed this patient's sepsis risk.
          </p>
        </GlassCard>
      )}
    </PageContainer>
  )
}
