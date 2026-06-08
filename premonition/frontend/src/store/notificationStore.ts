import { create } from 'zustand'

export type NotificationType = 'success' | 'error' | 'info' | 'warning'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message?: string
  duration?: number
}

interface NotificationState {
  items: Notification[]
  add: (n: Omit<Notification, 'id'>) => void
  remove: (id: string) => void
  success: (title: string, message?: string) => void
  error: (title: string, message?: string) => void
  info: (title: string, message?: string) => void
  warning: (title: string, message?: string) => void
}

let counter = 0

export const useNotificationStore = create<NotificationState>((set, get) => ({
  items: [],
  add: (n) => {
    const id = `notif-${++counter}`
    const item = { ...n, id }
    set({ items: [...get().items, item] })
    const duration = n.duration ?? 5000
    if (duration > 0) {
      setTimeout(() => get().remove(id), duration)
    }
  },
  remove: (id) => set({ items: get().items.filter((i) => i.id !== id) }),
  success: (title, message) => get().add({ type: 'success', title, message }),
  error: (title, message) => get().add({ type: 'error', title, message, duration: 8000 }),
  info: (title, message) => get().add({ type: 'info', title, message }),
  warning: (title, message) => get().add({ type: 'warning', title, message }),
}))
