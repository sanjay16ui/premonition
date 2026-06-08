import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'

describe('Sidebar', () => {
  it('renders PREMONITION brand', () => {
    render(<MemoryRouter><Sidebar /></MemoryRouter>)
    expect(screen.getByText(/PREMONITION/i)).toBeInTheDocument()
  })

  it('renders overview nav item', () => {
    render(<MemoryRouter><Sidebar /></MemoryRouter>)
    expect(screen.getByText('Overview')).toBeInTheDocument()
  })

  it('renders Live Patients nav item', () => {
    render(<MemoryRouter><Sidebar /></MemoryRouter>)
    expect(screen.getByText(/Live Patients/i)).toBeInTheDocument()
  })

  it('renders AI Copilot nav item', () => {
    render(<MemoryRouter><Sidebar /></MemoryRouter>)
    expect(screen.getByText(/AI Copilot/i)).toBeInTheDocument()
  })

  it('renders Analytics nav item', () => {
    // Ignore 3D canvas rendering timeout in JSDOM
    vi.stubGlobal('HTMLCanvasElement', { prototype: { getContext: () => ({}) } })
    render(<MemoryRouter><Sidebar /></MemoryRouter>)
    expect(screen.getByText(/Analytics/i)).toBeInTheDocument()
  })
})
