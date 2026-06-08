import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Stethoscope, FileText, ClipboardList, Download, Loader2 } from 'lucide-react'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { copilotApi } from '@/api/copilotEndpoints'
import { usePatientStore } from '@/store/patientStore'
import { exportPatientSummaryPDF, exportHandoverPDF } from '@/utils/pdfExport'

export function CopilotPatientPage() {
  const { selectedPatientId } = usePatientStore()
  const [patientId, setPatientId] = useState(selectedPatientId || 'patient-001')
  const [summary, setSummary] = useState('')
  const [handover, setHandover] = useState('')
  const [explanation, setExplanation] = useState('')

  const summaryMutation = useMutation({
    mutationFn: () => copilotApi.generateSummary(patientId),
    onSuccess: (d: any) => setSummary(d.message),
  })

  const handoverMutation = useMutation({
    mutationFn: () => copilotApi.handover({ patient_ids: [patientId] }),
    onSuccess: (d: any) => setHandover(d.message),
  })

  const explainMutation = useMutation({
    mutationFn: () => copilotApi.explainPrediction({ patient_id: patientId, risk_score: 0.55 }),
    onSuccess: (d: any) => setExplanation(d.message),
  })

  return (
    <PageContainer title="Patient Copilot" subtitle="AI summaries, handover notes, and prediction explanations — powered by Groq AI">
      {/* Patient ID Input */}
      <div className="mb-6 flex items-center gap-3">
        <input
          id="patient-id-input"
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          placeholder="Patient ID (e.g. patient-001)"
        />
        <div className="flex items-center gap-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2">
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
          <span className="text-xs font-semibold text-emerald-400">Groq AI</span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Patient Summary */}
        <GlassCard>
          <div className="mb-3 flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold text-slate-100">Patient Summary</h3>
          </div>
          <div className="mb-3 flex gap-2">
            <Button
              id="generate-summary-btn"
              onClick={() => summaryMutation.mutate()}
              disabled={summaryMutation.isPending}
            >
              {summaryMutation.isPending
                ? <><Loader2 className="h-4 w-4 animate-spin" /> Generating…</>
                : 'Generate Summary'}
            </Button>
            {summary && (
              <button
                id="export-summary-pdf-btn"
                onClick={() => exportPatientSummaryPDF(patientId, summary)}
                title="Export as PDF"
                className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400 transition-colors"
              >
                <Download className="h-3.5 w-3.5" /> PDF
              </button>
            )}
          </div>
          {summary ? (
            <div className="rounded-lg bg-slate-800/50 p-3 max-h-96 overflow-y-auto">
              <p className="whitespace-pre-wrap text-sm text-slate-300 leading-relaxed">{summary}</p>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">
              Click Generate Summary to get an enterprise-grade clinical assessment with vitals analysis, risk level, abnormal findings, and recommended actions.
            </p>
          )}
        </GlassCard>

        {/* Shift Handover */}
        <GlassCard>
          <div className="mb-3 flex items-center gap-2">
            <ClipboardList className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold text-slate-100">Shift Handover</h3>
          </div>
          <div className="mb-3 flex gap-2">
            <Button
              id="generate-handover-btn"
              onClick={() => handoverMutation.mutate()}
              disabled={handoverMutation.isPending}
            >
              {handoverMutation.isPending
                ? <><Loader2 className="h-4 w-4 animate-spin" /> Generating…</>
                : 'Generate Handover'}
            </Button>
            {handover && (
              <button
                id="export-handover-pdf-btn"
                onClick={() => exportHandoverPDF(handover)}
                title="Export as PDF"
                className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400 transition-colors"
              >
                <Download className="h-3.5 w-3.5" /> PDF
              </button>
            )}
          </div>
          {handover ? (
            <div className="rounded-lg bg-slate-800/50 p-3 max-h-96 overflow-y-auto">
              <p className="whitespace-pre-wrap text-sm text-slate-300 leading-relaxed">{handover}</p>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">
              Generate a formal shift handover report with Patient Overview, Clinical Events, Current Risks, Pending Actions, and Escalation Recommendations.
            </p>
          )}
        </GlassCard>

        {/* Prediction Explanation */}
        <GlassCard>
          <div className="mb-3 flex items-center gap-2">
            <FileText className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold text-slate-100">Prediction Explanation</h3>
          </div>
          <div className="mb-3">
            <Button
              id="explain-prediction-btn"
              onClick={() => explainMutation.mutate()}
              disabled={explainMutation.isPending}
            >
              {explainMutation.isPending
                ? <><Loader2 className="h-4 w-4 animate-spin" /> Explaining…</>
                : 'Explain Prediction'}
            </Button>
          </div>
          {explanation ? (
            <div className="rounded-lg bg-slate-800/50 p-3 max-h-96 overflow-y-auto">
              <p className="whitespace-pre-wrap text-sm text-slate-300 leading-relaxed">{explanation}</p>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">
              Get a full explanation of the ML prediction: Risk Score, Confidence, Top SHAP Factors, Trend Analysis, Clinical Meaning, and Recommended Actions.
            </p>
          )}
        </GlassCard>
      </div>
    </PageContainer>
  )
}
