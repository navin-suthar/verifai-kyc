import { useNavigate } from 'react-router-dom';
import { UserCheck } from 'lucide-react';
import {
  Card,
  EmptyState,
  ErrorState,
  PageHeader,
  ProgressBar,
  SkeletonTable,
  StatusBadge,
  Table,
  type Column,
} from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { listApplications } from '@/lib/api/applicationsApi';
import { documentTypeLabel, formatDateTime } from '@/lib/utils/format';
import { ROUTES } from '@/app/routes';
import type { ApplicationSummary } from '@/types/domain';

export default function ReviewPage() {
  const navigate = useNavigate();
  const { data, error, isLoading, reload } = useAsync(() => listApplications({ page: 1, pageSize: 50, status: 'needs_review' }));

  const columns: Column<ApplicationSummary>[] = [
    {
      key: 'applicant',
      header: 'Applicant',
      render: (r) => (
        <div>
          <p className="font-medium">{r.applicant_name ?? 'Unknown'}</p>
          <p className="font-mono text-xs text-fg-subtle">{r.customer_id}</p>
        </div>
      ),
    },
    { key: 'doc', header: 'Document', render: (r) => documentTypeLabel(r.document_type) },
    {
      key: 'conf',
      header: 'Confidence',
      render: (r) => (r.confidence === null ? '—' : <ProgressBar value={r.confidence} size="sm" />),
    },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'when', header: 'Updated', align: 'right', render: (r) => formatDateTime(r.updated_at) },
  ];

  return (
    <>
      <PageHeader
        title="Human review"
        description="Applications the model could not auto-decide. Approve, reject, or request more information."
      />
      <Card padded={false}>
        <div className="px-2 py-2">
          {error && !data ? (
            <ErrorState error={error} onRetry={reload} compact />
          ) : isLoading && !data ? (
            <div className="p-3">
              <SkeletonTable rows={6} cols={5} />
            </div>
          ) : (
            <Table
              columns={columns}
              rows={data?.items ?? []}
              rowKey={(r) => r.id}
              onRowClick={(r) => navigate(ROUTES.application(r.id))}
              emptyState={
                <EmptyState
                  icon={<UserCheck className="h-6 w-6" />}
                  title="Review queue is clear"
                  description="No applications are waiting for a human decision."
                />
              }
            />
          )}
        </div>
      </Card>
    </>
  );
}
