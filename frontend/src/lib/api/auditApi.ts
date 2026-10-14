import { apiClient } from './client';
import type { AuditLogEntry, Paginated } from '@/types/domain';

export interface ListAuditParams {
  page?: number;
  pageSize?: number;
  action?: string;
  actor?: string;
}

export async function listAuditLogs(params: ListAuditParams = {}): Promise<Paginated<AuditLogEntry>> {
  const search = new URLSearchParams();
  search.set('page', String(params.page ?? 1));
  search.set('page_size', String(params.pageSize ?? 25));
  if (params.action) search.set('action', params.action);
  if (params.actor) search.set('actor', params.actor);
  const { data } = await apiClient.get<Paginated<AuditLogEntry>>(`/audit?${search.toString()}`);
  return data;
}
