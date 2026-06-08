import { describe, it, expect, beforeEach } from 'vitest'
import { useNotificationStore } from '@/store/notificationStore'
import { useThemeStore } from '@/store/themeStore'

describe('notificationStore', () => {
  beforeEach(() => {
    useNotificationStore.setState({ items: [] })
  })

  it('adds and removes notifications', () => {
    useNotificationStore.getState().success('Test', 'Message')
    expect(useNotificationStore.getState().items).toHaveLength(1)
    const id = useNotificationStore.getState().items[0].id
    useNotificationStore.getState().remove(id)
    expect(useNotificationStore.getState().items).toHaveLength(0)
  })
})

describe('themeStore', () => {
  it('toggles theme mode', () => {
    useThemeStore.getState().setMode('light')
    expect(useThemeStore.getState().mode).toBe('light')
    useThemeStore.getState().toggle()
    expect(useThemeStore.getState().mode).toBe('dark')
  })
})
