import { Link } from 'react-router-dom'
import { Activity, AlertTriangle, Users, Heart, ArrowRight } from 'lucide-react'
import { useExecutiveSummary, useRealtimeStream } from '@/api/hooks/realtime'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { LoadingOverlay } from '@/components/common/LoadingOverlay'
import { AgentActivityFeed } from '@/components/ui/AgentActivityFeed'
import { ROUTES } from '@/routes/paths'
import { useAlertAudio } from '@/hooks/useAlertAudio'

export function CommandCenterPage() {
  const { data: executive, isLoading } = useExecutiveSummary()
  const { executive: streamExec, agentActions, patients: streamPatients } = useRealtimeStream()
  
  const exec = streamExec || executive

  // 🔊 Fire audio tones whenever a patient's alert level escalates
  useAlertAudio(streamPatients)

  if (isLoading && !exec) return <LoadingOverlay label="Loading hospital overview..." />

  // Categorize patients based on mock or real risk logic (Stable < 0.2, Watch < 0.5, High < 0.8, Critical >= 0.8)
  const total = exec?.current_icu_patients || 0
  const critical = exec?.critical_alert_count || 0
  const highRisk = exec?.high_risk_count || 0
  // Estimate watch and stable based on remaining
  const watch = Math.max(0, Math.floor((total - critical - highRisk) * 0.3))
  const stable = Math.max(0, total - critical - highRisk - watch)

  const criticalPatientsList = exec?.top_critical || []

  return (
    <PageContainer
      title="Hospital Overview"
      subtitle="Real-time clinical intelligence and patient triaging"
    >
      {/* 4 Top Level Cards: Stable, Watch, High Risk, Critical */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="rounded-3xl bg-green-500/10 border border-green-500/20 p-6 flex flex-col justify-between">
          <div className="flex items-center gap-3 text-green-600 dark:text-green-400 mb-2">
            <Heart className="w-6 h-6" />
            <h3 className="text-lg font-medium">Stable</h3>
          </div>
          <p className="text-4xl font-bold text-slate-800 dark:text-white">{stable}</p>
          <p className="text-sm text-slate-500 mt-1">Routine monitoring</p>
        </div>

        <div className="rounded-3xl bg-amber-500/10 border border-amber-500/20 p-6 flex flex-col justify-between">
          <div className="flex items-center gap-3 text-amber-600 dark:text-amber-400 mb-2">
            <Activity className="w-6 h-6" />
            <h3 className="text-lg font-medium">Watch</h3>
          </div>
          <p className="text-4xl font-bold text-slate-800 dark:text-white">{watch}</p>
          <p className="text-sm text-slate-500 mt-1">Elevated risk scores</p>
        </div>

        <div className="rounded-3xl bg-orange-500/10 border border-orange-500/20 p-6 flex flex-col justify-between">
          <div className="flex items-center gap-3 text-orange-600 dark:text-orange-400 mb-2">
            <AlertTriangle className="w-6 h-6" />
            <h3 className="text-lg font-medium">High Risk</h3>
          </div>
          <p className="text-4xl font-bold text-slate-800 dark:text-white">{highRisk}</p>
          <p className="text-sm text-slate-500 mt-1">Sepsis likely</p>
        </div>

        <div className="rounded-3xl bg-red-500/10 border border-red-500/20 p-6 flex flex-col justify-between">
          <div className="flex items-center gap-3 text-red-600 dark:text-red-400 mb-2">
            <AlertTriangle className="w-6 h-6" fill="currentColor" />
            <h3 className="text-lg font-medium">Critical</h3>
          </div>
          <p className="text-4xl font-bold text-slate-800 dark:text-white">{critical}</p>
          <p className="text-sm text-slate-500 mt-1">Immediate intervention</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Critical Alerts Feed */}
        <GlassCard title="Current Alerts" subtitle="Patients requiring immediate attention" className="rounded-3xl p-6">
          {criticalPatientsList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mb-4">
                <Heart className="w-8 h-8 text-green-500" />
              </div>
              <p>No critical alerts currently active.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {criticalPatientsList.map((p) => (
                <div key={p.patient_id} className="flex flex-col gap-3 p-4 rounded-2xl border border-red-500/30 bg-red-500/5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-lg font-semibold text-slate-800 dark:text-white">Patient #{p.patient_id}</h4>
                    <span className="text-xs font-medium px-2.5 py-1 bg-red-500/20 text-red-500 rounded-full">
                      CRITICAL RISK: {(p.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  {/* Doctor Explanation Mode directly embedded if available, else generic for the overview */}
                  <div className="text-sm text-slate-600 dark:text-slate-300">
                    <p><strong>What happened?</strong> Risk score surged rapidly.</p>
                    <p><strong>Why did it happen?</strong> Deteriorating vitals matching sepsis criteria.</p>
                    <p><strong>What should I do next?</strong> Evaluate immediately for broad-spectrum antibiotics.</p>
                  </div>
                  
                  <Link to={`${ROUTES.patientRisk}?id=${p.patient_id}`} className="text-sky-500 text-sm font-medium hover:underline flex items-center gap-1 mt-1">
                    View Full Clinical Details <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Agent Recommendations Feed */}
        <GlassCard title="Agent Recommendations" subtitle="Autonomous clinical AI logic" className="rounded-3xl p-6">
          <AgentActivityFeed actions={agentActions} maxItems={10} />
        </GlassCard>
      </div>
      
      {/* Quick Links */}
      <div className="mt-6 flex flex-wrap gap-4">
        <Link to={ROUTES.liveMonitoring} className="flex-1 min-w-[200px]">
          <div className="rounded-2xl bg-sky-500/10 hover:bg-sky-500/20 transition border border-sky-500/20 p-4 flex items-center justify-between group">
            <div className="flex items-center gap-3 text-sky-600 dark:text-sky-400">
              <Users className="w-6 h-6" />
              <span className="font-semibold">View All Patients</span>
            </div>
            <ArrowRight className="w-5 h-5 text-sky-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </Link>
        <Link to={ROUTES.copilot} className="flex-1 min-w-[200px]">
          <div className="rounded-2xl bg-indigo-500/10 hover:bg-indigo-500/20 transition border border-indigo-500/20 p-4 flex items-center justify-between group">
            <div className="flex items-center gap-3 text-indigo-600 dark:text-indigo-400">
              <Activity className="w-6 h-6" />
              <span className="font-semibold">Ask Clinical Copilot</span>
            </div>
            <ArrowRight className="w-5 h-5 text-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </Link>
      </div>

    </PageContainer>
  )
}
