import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AnalyticsLineChart } from '@/components/charts/AnalyticsLineChart'
import { AnalyticsBarChart } from '@/components/charts/AnalyticsBarChart'
import { AnalyticsPieChart } from '@/components/charts/AnalyticsPieChart'
import { AnalyticsHeatmap } from '@/components/charts/AnalyticsHeatmap'
import { ExecutiveKpiDashboard } from '@/components/charts/ExecutiveKpiDashboard'

describe('AnalyticsLineChart', () => {
  it('renders no data message when empty', () => {
    render(<AnalyticsLineChart data={[]} lines={['a']} />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('renders chart with data', () => {
    const { container } = render(
      <AnalyticsLineChart data={[{ label: 'A', value: 10 }]} lines={['value']} />,
    )
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })
})

describe('AnalyticsBarChart', () => {
  it('renders no data message when empty', () => {
    render(<AnalyticsBarChart data={[]} bars={['a']} />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('renders bar chart', () => {
    const { container } = render(
      <AnalyticsBarChart data={[{ label: 'B', count: 5 }]} bars={['count']} />,
    )
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })
})

describe('AnalyticsPieChart', () => {
  it('renders no data message when empty', () => {
    render(<AnalyticsPieChart data={[]} />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('renders pie chart', () => {
    const { container } = render(
      <AnalyticsPieChart data={[{ name: 'Low', value: 60 }]} />,
    )
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })

  it('renders donut chart with innerRadius', () => {
    const { container } = render(
      <AnalyticsPieChart data={[{ name: 'A', value: 50 }]} innerRadius={50} />,
    )
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy()
  })
})

describe('AnalyticsHeatmap', () => {
  it('renders heatmap cells', () => {
    const { container } = render(
      <AnalyticsHeatmap
        data={[[10, 20], [30, 40]]}
        rowLabels={['R1', 'R2']}
        colLabels={['C1', 'C2']}
      />,
    )
    expect(container.querySelectorAll('[title]').length).toBeGreaterThan(0)
  })
})

describe('ExecutiveKpiDashboard', () => {
  it('renders KPI cards', () => {
    render(
      <ExecutiveKpiDashboard
        kpis={[
          { label: 'Occupancy', value: '87', change: 3, unit: '%' },
          { label: 'Uptime', value: '99.9', change: 0.1, unit: '%' },
        ]}
      />,
    )
    expect(screen.getByText('Occupancy')).toBeInTheDocument()
    expect(screen.getByText('Uptime')).toBeInTheDocument()
  })

  it('shows positive change indicator', () => {
    render(
      <ExecutiveKpiDashboard kpis={[{ label: 'Test', value: '100', change: 5 }]} />,
    )
    expect(screen.getByText('+5%')).toBeInTheDocument()
  })
})
