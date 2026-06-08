import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Activity,
  ArrowRight,
  Brain,
  HeartPulse,
  Shield,
  TrendingUp,
  Users,
} from 'lucide-react'
import { useMetrics, useModelVersion, usePredictionHistory, useSystemStatus } from '@/api/hooks'
import { GlassCard } from '@/components/ui/GlassCard'
import { StatCard } from '@/components/ui/StatCard'
import { Button } from '@/components/ui/Button'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { LoadingOverlay } from '@/components/common/LoadingOverlay'
import { ErrorState } from '@/components/ui/ErrorState'
import { SepsisProbabilityChart } from '@/components/charts/SepsisProbabilityChart'
import { ROUTES } from '@/routes/paths'
import { formatPercent, formatRelativeTime } from '@/utils/format'
import { isHighRisk } from '@/utils/risk'

export function LandingPage() {
  const { data: status, isLoading: statusLoading, error: statusError } = useSystemStatus()
  const { data: metrics } = useMetrics()
  const { data: model } = useModelVersion()
  const { data: history } = usePredictionHistory({ limit: 20 })

  if (statusLoading) return <LoadingOverlay label="Connecting to PREMONITION..." />
  if (statusError) return <ErrorState message="Cannot reach the API. Start the backend with: python scripts/run_api.py" />

  const patients = history?.items || []
  const uniquePatients = new Set(patients.map((p) => p.patient_id)).size
  const highRisk = patients.filter((p) => isHighRisk(p.risk_score)).length
  const testMetrics = (model?.metrics as { test?: { pr_auc?: number; recall?: number } })?.test

  const chartData = patients.slice(0, 8).map((p) => ({
    patient: `#${p.patient_id}`,
    probability: p.risk_score,
    category: p.risk_score >= 0.6 ? 'red' : p.risk_score >= 0.35 ? 'orange' : p.risk_score >= 0.15 ? 'yellow' : 'green',
  }))

  return (
    <div className="p-4 lg:p-8">
      {/* Hero */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl gradient-bg p-8 lg:p-12 text-white"
      >
        <div className="relative z-10 max-w-2xl">
          <div className="mb-4 flex items-center gap-2">
            <HeartPulse className="h-8 w-8" />
            <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-medium">
              ICU Sepsis Early Warning System
            </span>
          </div>
          <h1 className="text-3xl font-bold lg:text-5xl">PREMONITION</h1>
          <p className="mt-4 text-lg text-white/90">
            AI that predicts sepsis in ICU patients <strong>hours before</strong> clinical
            symptoms appear — and explains <em>why</em> each patient is at risk.
          </p>
          <p className="mt-2 text-sm text-white/70">
            Sepsis is a life-threatening infection response. Early detection saves lives.
            PREMONITION monitors vital signs and lab data to flag at-risk patients automatically.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to={ROUTES.commandCenter}>
              <Button icon={<ArrowRight className="h-4 w-4" />}>
                Open Command Center
              </Button>
            </Link>
            <Link to={ROUTES.digitalTwin}>
              <Button variant="secondary">3D Digital Twin</Button>
            </Link>
            <Link to={ROUTES.patientRisk}>
              <Button variant="ghost">Run Prediction</Button>
            </Link>
          </div>
        </div>
        <div className="absolute -right-20 -top-20 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
      </motion.section>

      {/* CEO KPIs */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="System Status"
          value={status?.status === 'ready' ? 'Online' : 'Degraded'}
          icon={<Shield className="h-5 w-5" />}
          color={status?.model_loaded ? '#10b981' : '#ef4444'}
          tooltip="Whether the AI model is loaded and ready to make predictions"
          delay={0.1}
        />
        <StatCard
          label="Patients Monitored"
          value={uniquePatients || metrics?.predictions_total || 0}
          icon={<Users className="h-5 w-5" />}
          color="#0ea5e9"
          tooltip="Unique patients with recent risk assessments"
          delay={0.15}
        />
        <StatCard
          label="High-Risk Alerts"
          value={highRisk || metrics?.predictions_sepsis_alerts || 0}
          icon={<Activity className="h-5 w-5" />}
          color="#ef4444"
          tooltip="Patients flagged with elevated sepsis probability (60%+)"
          delay={0.2}
        />
        <StatCard
          label="Model Accuracy (PR-AUC)"
          value={testMetrics?.pr_auc ? formatPercent(testMetrics.pr_auc) : '—'}
          icon={<TrendingUp className="h-5 w-5" />}
          color="#8b5cf6"
          tooltip="Precision-Recall AUC on held-out test data — higher is better"
          delay={0.25}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Recent Predictions */}
        <GlassCard title="Recent Predictions" subtitle="Latest sepsis risk assessments" delay={0.3}>
          {patients.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">
              No predictions yet. Run one from the Patient Risk page.
            </p>
          ) : (
            <div className="space-y-3">
              {patients.slice(0, 5).map((p) => (
                <div
                  key={`${p.patient_id}-${p.timestamp}`}
                  className="flex items-center justify-between rounded-xl bg-slate-50 dark:bg-slate-800/50 p-3"
                >
                  <div>
                    <p className="font-medium">Patient #{p.patient_id}</p>
                    <p className="text-xs text-slate-400">
                      {formatRelativeTime(p.timestamp)} · {p.confidence} confidence
                    </p>
                  </div>
                  <RiskBadge
                    category={p.risk_score >= 0.6 ? 'red' : p.risk_score >= 0.35 ? 'orange' : 'green'}
                    score={p.risk_score}
                  />
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Explainability */}
        <GlassCard
          title="AI Explainability"
          subtitle="Why the model flagged each patient"
          delay={0.35}
        >
          <div className="flex items-start gap-3 mb-4">
            <Brain className="h-8 w-8 text-violet-500 shrink-0" />
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Every prediction includes a plain-language explanation powered by{' '}
              <strong>SHAP</strong> (a method that shows which patient measurements
              pushed the risk score up or down). No black-box decisions.
            </p>
          </div>
          {patients[0]?.explanation_summary && (
            <div className="rounded-xl bg-violet-500/10 border border-violet-500/20 p-4">
              <p className="text-xs text-violet-400 mb-1">Latest insight</p>
              <p className="text-sm">{patients[0].explanation_summary}</p>
            </div>
          )}
          <Link to={ROUTES.shapExplain} className="mt-4 inline-block">
            <Button variant="ghost" icon={<ArrowRight className="h-4 w-4" />}>
              Explore SHAP Explanations
            </Button>
          </Link>
        </GlassCard>
      </div>

      {/* Chart */}
      <GlassCard
        className="mt-6"
        title="Sepsis Probability by Patient"
        subtitle="Visual comparison of recent risk scores"
        delay={0.4}
      >
        <SepsisProbabilityChart data={chartData} />
      </GlassCard>
    </div>
  )
}
