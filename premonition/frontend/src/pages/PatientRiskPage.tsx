import { useState } from 'react'
import { Play, User } from 'lucide-react'
import { usePredict } from '@/api/hooks'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { FeatureImportanceChart } from '@/components/charts/FeatureImportanceChart'
import { SAMPLE_PATIENT, SAMPLE_PATIENT_LOW_RISK, SAMPLE_PATIENT_C } from '@/data/samplePatient'
import { useNotificationStore } from '@/store/notificationStore'
import { usePatientStore } from '@/store/patientStore'
import { RISK_DESCRIPTIONS } from '@/utils/risk'
import type { PatientFeatures } from '@/api/types'

export function PatientRiskPage() {
  const [patientId, setPatientId] = useState('37464')
  const [features, setFeatures] = useState<PatientFeatures>(SAMPLE_PATIENT)
  const predict = usePredict()
  const notify = useNotificationStore()
  const { setLastPrediction, addMonitoredPatient } = usePatientStore()

  const handlePredict = async () => {
    try {
      const result = await predict.mutateAsync({
        patient_id: patientId,
        features,
        include_shap: true,
        include_explanation: true,
      })
      setLastPrediction(result)
      addMonitoredPatient(String(patientId))
      notify.success('Prediction complete', `Risk: ${result.risk_pct}`)
    } catch (err) {
      notify.error('Prediction failed', err instanceof Error ? err.message : 'Unknown error')
    }
  }

  const result = predict.data
  const factorData =
    result?.top_factors.map((f) => ({
      feature: f.feature,
      contribution: f.contribution_pct,
      direction: f.direction,
    })) || []

  return (
    <PageContainer
      title="Patient Risk Analysis"
      subtitle="Assess sepsis risk for an individual ICU patient"
      action={
        <Button
          loading={predict.isPending}
          icon={<Play className="h-4 w-4" />}
          onClick={handlePredict}
        >
          Run Prediction
        </Button>
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard title="Patient Selection" subtitle="Choose a sample or enter patient ID">
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-500">Patient ID</label>
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                onClick={() => {
                  setPatientId('37464')
                  setFeatures(SAMPLE_PATIENT)
                }}
              >
                High-Risk (Patient A)
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setPatientId('34024')
                  setFeatures(SAMPLE_PATIENT_LOW_RISK)
                }}
              >
                Low-Risk (Patient B)
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setPatientId('30010')
                  setFeatures(SAMPLE_PATIENT_C)
                }}
              >
                Medium-Risk (Patient C)
              </Button>
            </div>
            <p className="text-xs text-slate-400">
              Samples use real ICU vitals from the training dataset. In production,
              vitals are pulled automatically from the hospital monitoring system.
            </p>
          </div>
        </GlassCard>

        <GlassCard title="Vital Signs Summary" subtitle="Key measurements used by the model">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <Vital label="Age" value={`${features.age} yrs`} />
            <Vital label="Heart Rate (avg)" value={`${features.hr_mean} bpm`} tooltip="Beats per minute — elevated rates may signal infection" />
            <Vital label="Temperature (avg)" value={`${features.temp_celsius_mean}°C`} tooltip="Body temperature — fever is a sepsis warning sign" />
            <Vital label="SpO2 (avg)" value={`${features.spo2_mean}%`} tooltip="Blood oxygen level — low values indicate respiratory distress" />
            <Vital label="Respiratory Rate" value={`${features.respiratory_rate_mean}/min`} />
            <Vital label="Systolic BP (avg)" value={`${features.sbp_mean} mmHg`} />
          </div>
        </GlassCard>
      </div>

      {result && (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <GlassCard title="Risk Assessment Result">
            <div className="flex items-center gap-4 mb-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-500/10">
                <User className="h-7 w-7 text-sky-500" />
              </div>
              <div>
                <p className="text-xl font-bold">Patient #{result.patient_id}</p>
                <RiskBadge category={result.risk_category} score={result.risk_score} />
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <Row label="Sepsis Probability" value={result.risk_pct} />
              <Row label="Alert Status" value={result.prediction_label === 'sepsis_alert' ? '⚠ Sepsis Alert' : '✓ No Alert'} />
              <Row label="Confidence" value={result.confidence} />
              <Row label="Model" value={`${result.model_name} v${result.model_version}`} />
            </div>
            <p className="mt-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 p-3 text-sm">
              {RISK_DESCRIPTIONS[result.risk_category as keyof typeof RISK_DESCRIPTIONS]}
            </p>
            {result.explanation_summary && (
              <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
                {result.explanation_summary}
              </p>
            )}
          </GlassCard>

          <GlassCard title="Top Contributing Factors" subtitle="What drove this risk score">
            <FeatureImportanceChart data={factorData} />
          </GlassCard>
        </div>
      )}

      {predict.isError && (
        <p className="mt-4 text-sm text-red-500">
          {predict.error?.message || 'Prediction failed. Is the API running?'}
        </p>
      )}
    </PageContainer>
  )
}

function Vital({ label, value, tooltip }: { label: string; value: string; tooltip?: string }) {
  return (
    <div className="rounded-xl bg-slate-50 dark:bg-slate-800/50 p-3">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="font-medium">{value}</p>
      {tooltip && <p className="mt-1 text-[10px] text-slate-400">{tooltip}</p>}
    </div>
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
