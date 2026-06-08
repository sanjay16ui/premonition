import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SettingsState {
  refreshInterval: number
  defaultTopN: number
  showTooltips: boolean
  apiBaseUrl: string
  setRefreshInterval: (ms: number) => void
  setDefaultTopN: (n: number) => void
  setShowTooltips: (show: boolean) => void
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      refreshInterval: 15_000,
      defaultTopN: 5,
      showTooltips: true,
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api/v1',
      setRefreshInterval: (ms) => set({ refreshInterval: ms }),
      setDefaultTopN: (n) => set({ defaultTopN: n }),
      setShowTooltips: (show) => set({ showTooltips: show }),
    }),
    { name: 'premonition-settings' },
  ),
)
