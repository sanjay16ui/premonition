import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface CacheState {
  patients: Record<string, unknown>;
  alerts: unknown[];
  lastSync: string | null;
  setPatients: (data: Record<string, unknown>) => void;
  setAlerts: (data: unknown[]) => void;
  persist: () => Promise<void>;
  restore: () => Promise<void>;
}

export const useCacheStore = create<CacheState>((set, get) => ({
  patients: {},
  alerts: [],
  lastSync: null,
  setPatients: (data) => set({ patients: data, lastSync: new Date().toISOString() }),
  setAlerts: (data) => set({ alerts: data, lastSync: new Date().toISOString() }),
  persist: async () => {
    const { patients, alerts, lastSync } = get();
    await AsyncStorage.setItem('offline_cache', JSON.stringify({ patients, alerts, lastSync }));
  },
  restore: async () => {
    const raw = await AsyncStorage.getItem('offline_cache');
    if (raw) {
      const data = JSON.parse(raw);
      set({ patients: data.patients, alerts: data.alerts, lastSync: data.lastSync });
    }
  },
}));
