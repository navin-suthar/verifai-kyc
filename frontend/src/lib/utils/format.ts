import type { ApplicationStatus, DocumentType } from '@/types/domain';

const dateTimeFormatter = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

const dateFormatter = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short' });

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : dateTimeFormatter.format(d);
}

export function formatShortDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : dateFormatter.format(d);
}

export function formatRelative(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.round(diffMs / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

export function formatPercent(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${value.toFixed(digits)}%`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  pending: 'Pending',
  processing: 'Processing',
  verified: 'Verified',
  rejected: 'Rejected',
  needs_review: 'Needs Review',
};

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  synthetic_pan: 'Synthetic PAN',
  synthetic_national_id: 'Synthetic National ID',
  synthetic_passport: 'Synthetic Passport',
  synthetic_utility_bill: 'Synthetic Utility Bill',
  unknown: 'Unknown',
};

export function statusLabel(status: ApplicationStatus): string {
  return STATUS_LABELS[status] ?? status;
}

export function documentTypeLabel(type: DocumentType): string {
  return DOCUMENT_TYPE_LABELS[type] ?? type;
}
