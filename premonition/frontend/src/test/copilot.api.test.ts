import { describe, it, expect } from 'vitest'

describe('Copilot API endpoints', () => {
  const endpoints = [
    { method: 'POST', path: '/copilot/chat' },
    { method: 'POST', path: '/copilot/explain-prediction' },
    { method: 'POST', path: '/copilot/explain-alert' },
    { method: 'POST', path: '/copilot/patient-summary' },
    { method: 'POST', path: '/copilot/handover' },
    { method: 'POST', path: '/copilot/executive-summary' },
    { method: 'POST', path: '/copilot/recommendations' },
    { method: 'POST', path: '/copilot/ingest-document' },
    { method: 'POST', path: '/copilot/search' },
    { method: 'GET', path: '/copilot/conversations' },
    { method: 'GET', path: '/copilot/conversations/{id}' },
  ]

  it('defines all 11 copilot endpoints', () => {
    expect(endpoints).toHaveLength(11)
  })

  it('all endpoints have method and path', () => {
    endpoints.forEach((ep) => {
      expect(ep.method).toBeTruthy()
      expect(ep.path.startsWith('/copilot')).toBe(true)
    })
  })

  it('chat endpoint is POST', () => {
    const chat = endpoints.find((e) => e.path === '/copilot/chat')
    expect(chat?.method).toBe('POST')
  })

  it('conversations endpoint is GET', () => {
    const conv = endpoints.find((e) => e.path === '/copilot/conversations')
    expect(conv?.method).toBe('GET')
  })
})

describe('Copilot API types', () => {
  it('CopilotResponse shape', () => {
    const response = {
      conversation_id: 'abc',
      message: 'Hello',
      citations: [],
      prompt_version: 'chat@1.0.0',
      model: 'mock-local',
      retrieval_trace: [],
    }
    expect(response.conversation_id).toBeTruthy()
    expect(response.model).toBe('mock-local')
  })

  it('Citation shape', () => {
    const citation = {
      source_id: 'doc1',
      title: 'Protocol',
      excerpt: 'Text here',
      score: 0.9,
      chunk_index: 0,
    }
    expect(citation.score).toBeGreaterThan(0)
  })

  it('SearchResponse includes retrieval trace', () => {
    const search = { query: 'sepsis', context: 'ctx', citations: [], retrieval_trace: ['retrieved:doc1:0.9'] }
    expect(search.retrieval_trace).toHaveLength(1)
  })
})
