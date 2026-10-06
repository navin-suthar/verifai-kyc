import { apiClient } from './client';
import { isSafeIdentifier } from '@/lib/security/sanitize';
import type { ApplicationDetail, ApplicationStatus, ApplicationSummary, Paginated } from '@/types/domain';

export interface ListApplicationsParams {
  page?: number;
  pageSize?: number;
  status?: ApplicationStatus | '';
  q?: string;
}

export async function listApplications(params: ListApplicationsParams = {}): Promise<Paginated<ApplicationSummary>> {
  const search = new URLSearchParams();
  search.set('page', String(params.page ?? 1));
  search.set('page_size', String(params.pageSize ?? 20));
  if (params.status) search.set('status', params.status);
  if (params.q?.trim()) search.set('q', params.q.trim().slice(0, 80));
  const { data } = await apiClient.get<Paginated<ApplicationSummary>>(`/applications?${search.toString()}`);
  return data;
}

export async function getApplication(id: string): Promise<ApplicationDetail> {
  if (!isSafeIdentifier(id)) throw { type: 'validation', message: 'Invalid application id.' };
  const { data } = await apiClient.get<ApplicationDetail>(`/applications/${encodeURIComponent(id)}`);
  return data;
}
