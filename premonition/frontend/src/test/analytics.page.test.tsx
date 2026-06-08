import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AnalyticsDashboardPage } from '@/pages/AnalyticsDashboardPage'
import { vi } from 'vitest'

vi.mock('@/api/hooks', () => ({
  useAnalyticsExecutive: () => ({ data: null }),
  useAnalyticsPopulation: () => ({ data: null }),
  useAnalyticsCapacity: () => ({ data: null }),
  useAnalyticsResources: () => ({ data: null }),
  useAnalyticsKPIs: () => ({ 
    data: { 
      sepsis_detection_rate: 0.95, 
      alert_response_time_min: 4.5, 
      model_uptime_pct: 99.9 
    } 
  }),
  useAnalyticsCompareModels: () => ({ data: null }),
  usePredictionHistory: () => ({ data: null }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('AnalyticsDashboardPage', () => {
  it('renders page title', () => {
    render(<AnalyticsDashboardPage />, { wrapper })
    expect(screen.getByText('Advanced Analytics')).toBeInTheDocument()
  })

  it('renders KPI section', () => {
    render(<AnalyticsDashboardPage />, { wrapper })
    expect(screen.getByText('Total Predictions')).toBeInTheDocument()
    expect(screen.getByText('Sepsis Detection Rate')).toBeInTheDocument()
  })

  it('renders chart sections', () => {
    render(<AnalyticsDashboardPage />, { wrapper })
    expect(screen.getByText('Risk Trend — 24h Rolling Window')).toBeInTheDocument()
    expect(screen.getByText('Model Performance')).toBeInTheDocument()
    expect(screen.getByText('Risk Distribution')).toBeInTheDocument()
  })

  it('renders all chart cards', () => {
    const { container } = render(<AnalyticsDashboardPage />, { wrapper })
    const cards = container.querySelectorAll('.rounded-2xl')
    expect(cards.length).toBeGreaterThanOrEqual(6)
  })
})
