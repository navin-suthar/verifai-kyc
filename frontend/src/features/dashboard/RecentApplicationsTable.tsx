import { useNavigate } from 'react-router-dom';
import { EmptyState, ProgressBar, StatusBadge, Table, type Column } from '@/components/ui';
import type { ApplicationSummary } from '@/types/domain';
import { documentTypeLabel, formatRelative } from '@/lib/utils/format';
import { ROUTES } from '@/app/routes';

interface RecentApplicationsTableProps {
  rows: ApplicationSummary[];
}

export default function RecentApplicationsTable({ rows }: RecentApplicationsTableProps) {
  const navigate = useNavigate();

  const columns: Column<ApplicationSummary>[] = [
    {
      key: 'customer',
      header: 'Customer',
      render: (r) => (
        <div>
          <p className="font-medium text-fg">{r.applicant_name ?? 'Unknown applicant'}</p>
          <p className="font-mono text-xs text-fg-subtle">{r.customer_id}</p>
        </div>
      ),
    },
    {
      key: 'document',
      header: 'Document',
      render: (r) => (
        <div>
          <p className="text-fg">{documentTypeLabel(r.document_type)}</p>
          <p className="font-mono text-xs text-fg-subtle">{r.document_number_masked ?? '—'}</p>
        </div>
      ),
    },
    {
      key: 'confidence',
      header: 'Confidence',
      className: 'w-40',
      render: (r) =>
        r.confidence === null ? (
          <span className="text-xs text-fg-subtle">Pending</span>
        ) : (
          <ProgressBar value={r.confidence} size="sm" />
        ),
    },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    {
      key: 'updated',
      header: 'Updated',
      align: 'right',
      render: (r) => <span className="text-xs text-fg-muted">{formatRelative(r.updated_at)}</span>,
    },
  ];

  return (
    <Table
      columns={columns}
      rows={rows}
      rowKey={(r) => r.id}
      onRowClick={(r) => navigate(ROUTES.application(r.id))}
      emptyState={<EmptyState title="No applications yet" description="Upload a synthetic KYC document to see it here." />}
    />
  );
}
