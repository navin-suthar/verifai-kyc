import { apiClient } from './client';
import type { AnalyticsSummary, PublicSettings } from '@/types/domain';

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const { data } = await apiClient.get<AnalyticsSummary>('/analytics/summary');
  return data;
}

export async function getPublicSettings(): Promise<PublicSettings> {
  const { data } = await apiClient.get<PublicSettings>('/settings/public');
  return data;
}
