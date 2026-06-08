import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { RiskTrendChart } from '@/components/charts/RiskTrendChart'
import { SepsisProbabilityChart } from '@/components/charts/SepsisProbabilityChart'
import { FeatureImportanceChart } from '@/components/charts/FeatureImportanceChart'
import { SystemMetricsChart } from '@/components/charts/SystemMetricsChart'
import { PredictionTimelineChart } from '@/components/charts/PredictionTimelineChart'
import { ModelPerformanceChart } from '@/components/charts/ModelPerformanceChart'
import { ShapContributionChart } from '@/components/charts/ShapContributionChart'

const sampleTrend = [{ time: '10:00', risk: 0.5 }, { time: '11:00', risk: 0.7 }]
const sampleProb = [{ patient: 'P1', probability: 0.3, category: 'low' }, { patient: 'P2', probability: 0.6, category: 'high' }]
const sampleFeatures = [{ feature: 'hr_mean', contribution: 0.25, direction: 'positive' }, { feature: 'lactate', contribution: 0.35, direction: 'positive' }]
const sampleMetrics = [{ label: '10:00', predictions: 45, alerts: 3, errors: 0 }, { label: '11:00', predictions: 62, alerts: 5, errors: 1 }]
const sampleTimeline = [{ time: '10:00', alerts: 2, total: 15 }]
const sampleModel = [{ model: 'XGBoost', pr_auc: 0.89, recall: 0.85, f1: 0.87, roc_auc: 0.94 }]
const sampleShap = [{ feature: 'lactate', value: 0.3 }, { feature: 'hr', value: -0.1 }]

describe('Extended chart components', () => {
  it('RiskTrendChart renders with data', () => {
    const { container } = render(<RiskTrendChart data={sampleTrend} />)
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })

  it('RiskTrendChart shows empty state', () => {
    const { getByText } = render(<RiskTrendChart data={[]} />)
    expect(getByText(/No risk trend/i)).toBeInTheDocument()
  })

  it('SepsisProbabilityChart renders', () => {
    const { container } = render(<SepsisProbabilityChart data={sampleProb} />)
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })

  it('FeatureImportanceChart renders', () => {
    const { container } = render(<FeatureImportanceChart data={sampleFeatures} />)
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })

  it('SystemMetricsChart renders', () => {
    const { container } = render(<SystemMetricsChart data={sampleMetrics} />)
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })

  it('PredictionTimelineChart renders', () => {
    const { container } = render(<PredictionTimelineChart data={sampleTimeline} />)
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })

  it('ModelPerformanceChart renders', () => {
    const { container } = render(<ModelPerformanceChart data={sampleModel} />)
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })

  it('ShapContributionChart renders', () => {
    const { container } = render(<ShapContributionChart data={sampleShap} />)
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })
})
