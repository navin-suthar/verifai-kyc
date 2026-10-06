import { apiClient } from './client';
import { env } from '@/config/env';
import type { CurrentUser } from '@/types/domain';

export interface LoginRequest {
  username: string;
  password: string;
}

const MOCK_USER: CurrentUser = { username: 'demo.analyst', role: 'reviewer', display_name: 'Demo Analyst' };
let mockSession: CurrentUser | null = null;

export async function login(payload: LoginRequest): Promise<CurrentUser> {
  if (env.useMocks) {
    mockSession = MOCK_USER;
    return MOCK_USER;
  }
  const { data } = await apiClient.post<CurrentUser>('/auth/login', payload);
  return data;
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  if (env.useMocks) return mockSession;
  try {
    const { data } = await apiClient.get<CurrentUser>('/auth/me');
    return data;
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  if (env.useMocks) {
    mockSession = null;
    return;
  }
  await apiClient.post('/auth/logout');
}
