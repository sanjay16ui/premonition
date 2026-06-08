import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'

// Mock smooth scrolling which JSDOM doesn't support
window.HTMLElement.prototype.scrollIntoView = vi.fn()

// Mock IntersectionObserver which JSDOM doesn't support
class MockIntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver
})
