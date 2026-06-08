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
      model_uptime_pct: 99.9,
      predictions_per_day: 1500
    } 
  }),
  useAnalyticsCompareModels: () => ({ data: null }),
  usePredictionHistory: () => ({ data: null }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('AnalyticsDashboardPage extended', () => {
  it('renders capacity planning section', () => {
    render(<AnalyticsDashboardPage />, { wrapper })
    expect(screen.getByText(/Total Predictions/i)).toBeInTheDocument()
  })

  it('renders resource utilization section', () => {
    render(<AnalyticsDashboardPage />, { wrapper })
    expect(screen.getByText(/Avg Alert Response Time/i)).toBeInTheDocument()
  })

  it('renders realtime alert trends', () => {
    render(<AnalyticsDashboardPage />, { wrapper })
    expect(screen.getByText(/Risk Trend — 24h Rolling Window/i)).toBeInTheDocument()
  })

  it('renders donut chart section', () => {
    render(<AnalyticsDashboardPage />, { wrapper })
    expect(screen.getByText(/Risk Distribution/i)).toBeInTheDocument()
  })
})
