import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ChatInterface } from '@/components/copilot/ChatInterface'
import { CitationPanel } from '@/components/copilot/CitationPanel'
import { ConversationHistory } from '@/components/copilot/ConversationHistory'
import { ROUTES } from '@/routes/paths'

describe('Copilot routes', () => {
  it('defines copilot paths', () => {
    expect(ROUTES.copilot).toBe('/copilot')
    expect(ROUTES.copilotPatient).toBe('/copilot/patient')
    expect(ROUTES.copilotExecutive).toBe('/copilot/executive')
  })
})

describe('ChatInterface', () => {
  it('renders empty state', () => {
    render(<ChatInterface messages={[]} onSend={() => {}} isLoading={false} />)
    expect(screen.getByText(/AI Clinical Copilot/i)).toBeTruthy()
  })

  it('renders messages', () => {
    render(<ChatInterface messages={[
      { id: '1', timestamp: '1', role: 'user', content: 'Hello' },
      { id: '2', timestamp: '2', role: 'assistant', content: 'Hi there' },
    ]} onSend={() => {}} isLoading={false} />)
    expect(screen.getByText('Hello')).toBeTruthy()
    expect(screen.getByText('Hi there')).toBeTruthy()
  })

  it('calls onSend on submit', () => {
    let sent = ''
    render(<ChatInterface messages={[]} onSend={(m) => { sent = m }} isLoading={false} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'test message' } })
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })
    expect(sent).toBe('test message')
  })

  it('shows citations', () => {
    render(<ChatInterface messages={[{
      id: '3', timestamp: '3',
      role: 'assistant',
      content: 'Answer',
      citations: [{ source_id: 's1', title: 'Sepsis-3', excerpt: 'text', score: 0.9, chunk_index: 0 }],
    }]} onSend={() => {}} isLoading={false} />)
    expect(screen.getByText(/Sepsis-3/)).toBeTruthy()
  })

  it('disables send button when loading', () => {
    render(<ChatInterface messages={[]} onSend={() => {}} isLoading={true} />)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})

describe('CitationPanel', () => {
  it('renders nothing without citation', () => {
    const { container } = render(<CitationPanel citation={null} onClose={() => {}} />)
    expect(container.textContent).toBe('')
  })

  it('renders citation details', () => {
    render(<CitationPanel
      citation={{ source_id: 'doc1', title: 'SSC Bundle', excerpt: 'Antibiotics within 1 hour', score: 0.85, chunk_index: 0 }}
      onClose={() => {}}
    />)
    expect(screen.getByText('SSC Bundle')).toBeTruthy()
    expect(screen.getByText(/Antibiotics within 1 hour/)).toBeTruthy()
    expect(screen.getByText(/85.0%/)).toBeTruthy()
  })

  it('calls onClose', () => {
    let closed = false
    render(<CitationPanel
      citation={{ source_id: 'd', title: 'T', excerpt: 'E', score: 0.5, chunk_index: 0 }}
      onClose={() => { closed = true }}
    />)
    fireEvent.click(screen.getByRole('button'))
    expect(closed).toBe(true)
  })
})

describe('ConversationHistory', () => {
  it('shows empty state', () => {
    render(<ConversationHistory conversations={[]} onSelect={() => {}} />)
    expect(screen.getByText(/No conversations yet/)).toBeTruthy()
  })

  it('renders conversations', () => {
    render(<ConversationHistory
      conversations={[{ id: 'c1', title: 'Sepsis question', message_count: 4, created_at: '', updated_at: '' }]}
      onSelect={() => {}}
    />)
    expect(screen.getByText('Sepsis question')).toBeTruthy()
    expect(screen.getByText('4 messages')).toBeTruthy()
  })

  it('calls onSelect', () => {
    let selected = ''
    render(<ConversationHistory
      conversations={[{ id: 'c1', title: 'Test', message_count: 2, created_at: '', updated_at: '' }]}
      onSelect={(id) => { selected = id }}
    />)
    fireEvent.click(screen.getByText('Test'))
    expect(selected).toBe('c1')
  })

  it('highlights active conversation', () => {
    const { container } = render(<ConversationHistory
      conversations={[{ id: 'c1', title: 'Active', message_count: 1, created_at: '', updated_at: '' }]}
      activeId="c1"
      onSelect={() => {}}
    />)
    expect(container.innerHTML).toContain('indigo')
  })
})
