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

export async function uploadApplication(file: File): Promise<ApplicationDetail> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await apiClient.post<ApplicationDetail>('/applications', form, { timeout: 120_000 });
  return data;
}

export async function submitReview(
  id: string,
  decision: 'approve' | 'reject' | 'request_info',
  notes?: string,
): Promise<ApplicationDetail> {
  if (!isSafeIdentifier(id)) throw { type: 'validation', message: 'Invalid application id.' };
  const { data } = await apiClient.post<ApplicationDetail>(`/applications/${encodeURIComponent(id)}/review`, {
    decision,
    notes: notes?.trim() || null,
  });
  return data;
}

export function documentPreviewUrl(id: string): string {
  return `/api/applications/${encodeURIComponent(id)}/document`;
}
