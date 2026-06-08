import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatCard } from '@/components/ui/StatCard'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'

describe('UI Components', () => {
  it('renders StatCard', () => {
    render(<StatCard label="Test Metric" value={42} />)
    expect(screen.getByText('Test Metric')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders RiskBadge', () => {
    render(<RiskBadge category="red" score={0.85} />)
    expect(screen.getByText(/Critical Risk/)).toBeInTheDocument()
  })

  it('renders EmptyState', () => {
    render(
      <EmptyState title="No data" description="Nothing here yet" />,
    )
    expect(screen.getByText('No data')).toBeInTheDocument()
    expect(screen.getByText('Nothing here yet')).toBeInTheDocument()
  })

  it('renders Button', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })
})
