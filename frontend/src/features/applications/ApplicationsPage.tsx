import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Upload } from 'lucide-react';
import {
  Card,
  EmptyState,
  ErrorState,
  Input,
  LinkButton,
  PageHeader,
  Pagination,
  ProgressBar,
  Select,
  SkeletonTable,
  StatusBadge,
  Table,
  type Column,
} from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { listApplications } from '@/lib/api/applicationsApi';
import { documentTypeLabel, formatDateTime, STATUS_LABELS } from '@/lib/utils/format';
import { APPLICATION_STATUSES, type ApplicationStatus, type ApplicationSummary } from '@/types/domain';
import { ROUTES } from '@/app/routes';

const PAGE_SIZE = 10;

const STATUS_OPTIONS = APPLICATION_STATUSES.map((s) => ({ value: s, label: STATUS_LABELS[s] }));

function isStatus(value: string | null): value is ApplicationStatus {
  return !!value && (APPLICATION_STATUSES as readonly string[]).includes(value);
}

export default function ApplicationsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const statusParam = searchParams.get('status');
  const status: ApplicationStatus | '' = isStatus(statusParam) ? statusParam : '';
  const page = Math.max(1, Number(searchParams.get('page') ?? 1));
  const [query, setQuery] = useState(searchParams.get('q') ?? '');
  const debouncedQuery = useDebouncedValue(query, 350);

  const { data, error, isLoading, reload } = useAsync(
    () => listApplications({ page, pageSize: PAGE_SIZE, status, q: debouncedQuery }),
    [page, status, debouncedQuery],
  );

  const updateParams = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setSearchParams(next, { replace: true });
  };

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
        r.confidence === null ? <span className="text-xs text-fg-subtle">Pending</span> : <ProgressBar value={r.confidence} size="sm" />,
    },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'created', header: 'Submitted', align: 'right', render: (r) => <span className="text-xs text-fg-muted">{formatDateTime(r.created_at)}</span> },
  ];

  return (
    <>
      <PageHeader
        title="Applications"
        description="Every synthetic KYC application processed by the pipeline."
        actions={
          <LinkButton to={ROUTES.upload} leftIcon={<Upload className="h-4 w-4" />}>
            Upload document
          </LinkButton>
        }
      />

      <Card padded={false}>
        <div className="flex flex-col gap-3 border-b p-4 sm:flex-row sm:items-center">
          <div className="flex-1">
            <label htmlFor="app-search" className="sr-only">
              Search by customer id or name
            </label>
            <Input
              id="app-search"
              type="search"
              placeholder="Search customer id or name…"
              maxLength={80}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                updateParams({ q: e.target.value || null, page: null });
              }}
              leftIcon={<Search className="h-4 w-4" />}
            />
          </div>
          <div className="sm:w-52">
            <label htmlFor="app-status" className="sr-only">
              Filter by status
            </label>
            <Select
              id="app-status"
              value={status}
              options={STATUS_OPTIONS}
              placeholder="All statuses"
              onChange={(e) => updateParams({ status: e.target.value || null, page: null })}
            />
          </div>
        </div>

        <div className="px-2 py-2">
          {error && !data ? (
            <ErrorState error={error} onRetry={reload} compact />
          ) : isLoading && !data ? (
            <div className="p-3">
              <SkeletonTable rows={8} cols={5} />
            </div>
          ) : (
            <Table
              columns={columns}
              rows={data?.items ?? []}
              rowKey={(r) => r.id}
              onRowClick={(r) => navigate(ROUTES.application(r.id))}
              emptyState={
                <EmptyState
                  title="No applications match"
                  description="Try a different search term or status filter, or upload a new synthetic document."
                />
              }
            />
          )}
        </div>

        {data && data.total > 0 && (
          <div className="border-t px-4 py-3">
            <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPageChange={(p) => updateParams({ page: String(p) })} />
          </div>
        )}
      </Card>
    </>
  );
}
