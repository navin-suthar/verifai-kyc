import { useState } from 'react';
import { Card, EmptyState, ErrorState, Input, PageHeader, Pagination, Select, SkeletonTable, Table, type Column } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { listAuditLogs } from '@/lib/api/auditApi';
import { formatDateTime } from '@/lib/utils/format';
import type { AuditLogEntry } from '@/types/domain';

const ACTION_OPTIONS = [
  { value: 'auth.login', label: 'Login' },
  { value: 'document.uploaded', label: 'Document uploaded' },
  { value: 'pipeline.decision_made', label: 'Decision made' },
  { value: 'review.submitted', label: 'Review submitted' },
  { value: 'assistant.query', label: 'Assistant query' },
];

export default function AuditPage() {
  const [page, setPage] = useState(1);
  const [action, setAction] = useState('');
  const [actor, setActor] = useState('');
  const { data, error, isLoading, reload } = useAsync(
    () => listAuditLogs({ page, pageSize: 20, action, actor }),
    [page, action, actor],
  );

  const columns: Column<AuditLogEntry>[] = [
    { key: 'ts', header: 'When', render: (r) => <span className="text-xs">{formatDateTime(r.timestamp)}</span> },
    { key: 'actor', header: 'Actor', render: (r) => <span className="font-medium">{r.actor}</span> },
    { key: 'action', header: 'Action', render: (r) => <span className="font-mono text-xs">{r.action}</span> },
    {
      key: 'entity',
      header: 'Entity',
      render: (r) => (
        <span className="text-xs text-fg-muted">
          {r.entity_type}
          {r.entity_id ? ` · ${r.entity_id.slice(0, 8)}` : ''}
        </span>
      ),
    },
  ];

  return (
    <>
      <PageHeader title="Audit logs" description="Append-only trail of authentication, pipeline and reviewer events. Raw document numbers are never stored here." />
      <Card padded={false}>
        <div className="flex flex-col gap-3 border-b p-4 sm:flex-row">
          <Input
            placeholder="Filter by actor…"
            maxLength={80}
            value={actor}
            onChange={(e) => {
              setActor(e.target.value);
              setPage(1);
            }}
          />
          <Select
            value={action}
            options={ACTION_OPTIONS}
            placeholder="All actions"
            onChange={(e) => {
              setAction(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="px-2 py-2">
          {error && !data ? (
            <ErrorState error={error} onRetry={reload} compact />
          ) : isLoading && !data ? (
            <div className="p-3">
              <SkeletonTable rows={8} cols={4} />
            </div>
          ) : (
            <Table
              columns={columns}
              rows={data?.items ?? []}
              rowKey={(r) => r.id}
              emptyState={<EmptyState title="No audit events" description="Events appear as you use the demo." />}
            />
          )}
        </div>
        {data && data.total > 0 && (
          <div className="border-t px-4 py-3">
            <Pagination page={page} pageSize={20} total={data.total} onPageChange={setPage} />
          </div>
        )}
      </Card>
    </>
  );
}
