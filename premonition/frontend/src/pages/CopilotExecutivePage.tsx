import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Building2, Lightbulb } from 'lucide-react'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { copilotApi } from '@/api/copilotEndpoints'

export function CopilotExecutivePage() {
  const [executiveReport, setExecutiveReport] = useState('')
  const [recommendations, setRecommendations] = useState('')

  const execMutation = useMutation({
    mutationFn: () => copilotApi.executiveSummary({ include_kpis: true }),
    onSuccess: (d) => setExecutiveReport(d.message),
  })

  const recMutation = useMutation({
    mutationFn: () => copilotApi.recommendations({ risk_score: 0.4 }),
    onSuccess: (d) => setRecommendations(d.message),
  })

  return (
    <PageContainer title="Executive Copilot" subtitle="AI-powered hospital status and strategic insights">
      <div className="grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <div className="mb-3 flex items-center gap-2">
            <Building2 className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold">Hospital Status Summary</h3>
          </div>
          <Button onClick={() => execMutation.mutate()} disabled={execMutation.isPending} className="mb-3">
            Generate Executive Summary
          </Button>
          <p className="whitespace-pre-wrap text-sm text-slate-600 dark:text-slate-300">
            {executiveReport || 'Click to generate hospital-wide status report...'}
          </p>
        </GlassCard>
        <GlassCard>
          <div className="mb-3 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold">Strategic Recommendations</h3>
          </div>
          <Button onClick={() => recMutation.mutate()} disabled={recMutation.isPending} className="mb-3">
            Generate Recommendations
          </Button>
          <p className="whitespace-pre-wrap text-sm text-slate-600 dark:text-slate-300">
            {recommendations || 'Click to generate recommendations...'}
          </p>
        </GlassCard>
      </div>
    </PageContainer>
  )
}
