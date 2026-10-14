import { Card, CardHeader, ErrorState, PageHeader, Skeleton } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { getAnalyticsSummary } from '@/lib/api/analyticsApi';
import { formatPercent } from '@/lib/utils/format';
import StatCard from '@/features/dashboard/StatCard';
import VolumeChart from '@/features/dashboard/charts/VolumeChart';
import StatusDonut from '@/features/dashboard/charts/StatusDonut';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Brain, CheckCircle2, Gauge, Scale, UserCheck, XCircle } from 'lucide-react';

export default function AnalyticsPage() {
  const { data, error, isLoading, reload } = useAsync(getAnalyticsSummary);

  if (error && !data) {
    return (
      <>
        <PageHeader title="Analytics" />
        <ErrorState error={error} onRetry={reload} />
      </>
    );
  }

  const loading = isLoading && !data;

  return (
    <>
      <PageHeader
        title="Analytics"
        description="Pipeline performance, AI confidence and human-in-the-loop volume for this synthetic workspace."
      />

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <StatCard label="Applications" value={String(data?.total_applications ?? 0)} icon={<Scale className="h-5 w-5" />} isLoading={loading} />
        <StatCard label="Verified" value={String(data?.verified ?? 0)} tone="success" icon={<CheckCircle2 className="h-5 w-5" />} isLoading={loading} />
        <StatCard label="Rejected" value={String(data?.rejected ?? 0)} tone="danger" icon={<XCircle className="h-5 w-5" />} isLoading={loading} />
        <StatCard label="Human reviewed" value={String(data?.human_reviewed ?? 0)} tone="warning" icon={<UserCheck className="h-5 w-5" />} isLoading={loading} />
        <StatCard label="Avg. confidence" value={formatPercent(data?.average_confidence, 1)} tone="info" icon={<Gauge className="h-5 w-5" />} isLoading={loading} />
        <StatCard label="Auto-verify share" value={formatPercent(data?.auto_verified_share, 1)} tone="brand" icon={<Brain className="h-5 w-5" />} isLoading={loading} />
      </section>

      <section className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-5">
        <Card className="xl:col-span-3">
          <CardHeader title="Daily outcomes" description="Last 14 days" />
          {loading || !data ? <Skeleton className="h-72" /> : <VolumeChart data={data.daily_volume} />}
        </Card>
        <Card className="xl:col-span-2">
          <CardHeader title="Status mix" />
          {loading || !data ? <Skeleton className="h-72" /> : <StatusDonut data={data.status_breakdown} total={data.total_applications} />}
        </Card>
      </section>

      <section className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Average confidence by status" />
          {loading || !data ? (
            <Skeleton className="h-64" />
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.confidence_by_status}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--c-line)" />
                  <XAxis dataKey="status" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="average_confidence" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
        <Card>
          <CardHeader title="Document types" />
          {loading || !data ? (
            <Skeleton className="h-64" />
          ) : (
            <ul className="space-y-3">
              {data.document_types.map((row) => (
                <li key={row.document_type} className="flex items-center justify-between text-sm">
                  <span className="text-fg-muted">{row.document_type.replaceAll('_', ' ')}</span>
                  <span className="font-medium tabular-nums">{row.count}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </section>

      {data && (
        <p className="mt-6 text-xs text-fg-subtle">
          Thresholds: auto-verify ≥ {data.thresholds.auto_verify_min}% · review ≥ {data.thresholds.review_min}%. Change them via environment variables without code changes.
        </p>
      )}
    </>
  );
}
