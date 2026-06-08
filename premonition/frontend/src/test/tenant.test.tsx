import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TenantManagementPage } from '@/pages/TenantManagementPage'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({
      data: {
        count: 2,
        items: [
          { id: 't-1', hospital_name: 'City Hospital', slug: 'city', status: 'active', bed_capacity: 200, icu_beds: 40 },
          { id: 't-2', hospital_name: 'Regional ICU', slug: 'regional', status: 'active', bed_capacity: 100, icu_beds: 20 },
        ],
      },
    }),
  },
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('TenantManagementPage', () => {
  it('renders page title', async () => {
    render(<TenantManagementPage />, { wrapper })
    expect(screen.getByText('Tenant Management')).toBeInTheDocument()
  })

  it('loads and displays tenants', async () => {
    render(<TenantManagementPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText('City Hospital')).toBeInTheDocument()
      expect(screen.getByText('Regional ICU')).toBeInTheDocument()
    })
  })

  it('shows tenant status badges', async () => {
    render(<TenantManagementPage />, { wrapper })
    await waitFor(() => {
      const badges = screen.getAllByText('active')
      expect(badges.length).toBeGreaterThan(0)
    })
  })
})
