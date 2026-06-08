import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface ThemeState {
  isDark: boolean;
  toggle: () => void;
  init: () => Promise<void>;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  isDark: true,
  toggle: () => {
    const next = !get().isDark;
    set({ isDark: next });
    AsyncStorage.setItem('theme', next ? 'dark' : 'light');
  },
  init: async () => {
    const saved = await AsyncStorage.getItem('theme');
    if (saved) set({ isDark: saved === 'dark' });
  },
}));
