/* Lightweight API client. */
import axios from 'axios';

export const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export function setAuthToken(token: string | null) {
  if (token) api.defaults.headers.common.Authorization = `Bearer ${token}`;
  else delete api.defaults.headers.common.Authorization;
}

export function loadToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem('ml_access');
}

export function saveTokens(access: string, refresh: string) {
  window.localStorage.setItem('ml_access', access);
  window.localStorage.setItem('ml_refresh', refresh);
  setAuthToken(access);
}

export function clearTokens() {
  window.localStorage.removeItem('ml_access');
  window.localStorage.removeItem('ml_refresh');
  setAuthToken(null);
}
