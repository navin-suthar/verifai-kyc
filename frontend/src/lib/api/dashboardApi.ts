import { apiClient } from './client';
import { env } from '@/config/env';
import type { DashboardSummary } from '@/types/domain';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getSummaryMock(): Promise<DashboardSummary> {
  const { mockDashboard } = await import('@/mocks/data');
  await delay(400);
  return mockDashboard;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  if (env.useMocks) return getSummaryMock();
  const { data } = await apiClient.get<DashboardSummary>('/dashboard/summary');
  return data;
}
