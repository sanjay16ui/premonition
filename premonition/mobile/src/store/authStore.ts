import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { login as apiLogin } from '../api/client';

interface AuthState {
  isAuthenticated: boolean;
  email: string | null;
  role: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  email: null,
  role: null,
  login: async (email, password) => {
    const data = await apiLogin(email, password);
    set({ isAuthenticated: true, email, role: data.role });
  },
  logout: async () => {
    await SecureStore.deleteItemAsync('access_token');
    set({ isAuthenticated: false, email: null, role: null });
  },
}));
