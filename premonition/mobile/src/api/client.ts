import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('access_token');
  const tenantId = await SecureStore.getItemAsync('tenant_id');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (tenantId) config.headers['X-Tenant-ID'] = tenantId;
  return config;
});

export async function login(email: string, password: string) {
  const { data } = await apiClient.post('/auth/login', { email, password });
  await SecureStore.setItemAsync('access_token', data.access_token);
  return data;
}

export async function getHealth() {
  const { data } = await apiClient.get('/health');
  return data;
}

export async function getDashboardMetrics() {
  const { data } = await apiClient.get('/metrics/summary');
  return data;
}

export async function getAlerts() {
  const { data } = await apiClient.get('/realtime/alerts');
  return data;
}

export async function getPatientRisk(patientId: string) {
  const { data } = await apiClient.get(`/realtime/patients/${patientId}`);
  return data;
}

export async function copilotChat(message: string) {
  const { data } = await apiClient.post('/copilot/chat', { message });
  return data;
}

export async function getExecutiveSummary() {
  const { data } = await apiClient.post('/copilot/executive-summary', {});
  return data;
}
