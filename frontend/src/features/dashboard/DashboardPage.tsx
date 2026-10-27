import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Clock3, FileStack, Gauge, TrendingUp, Upload, XCircle } from 'lucide-react';
import { Card, CardHeader, ErrorState, LinkButton, PageHeader, Skeleton, SkeletonTable } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { getDashboardSummary } from '@/lib/api/dashboardApi';
import { formatPercent } from '@/lib/utils/format';
import { ROUTES } from '@/app/routes';
import StatCard from './StatCard';
import VolumeChart from './charts/VolumeChart';
import StatusDonut from './charts/StatusDonut';
import RecentApplicationsTable from './RecentApplicationsTable';

export default function DashboardPage() {
  const { data, error, isLoading, reload } = useAsync(getDashboardSummary);

  if (error && !data) {
    return (
      <>
        <PageHeader title="Dashboard" description="Live overview of the KYC verification pipeline." />
        <ErrorState error={error} onRetry={reload} />
      </>
    );
  }

  const s = data;
  const loading = isLoading && !data;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Live overview of the KYC verification pipeline."
        actions={
          <LinkButton to={ROUTES.upload} leftIcon={<Upload className="h-4 w-4" />}>
            Upload document
          </LinkButton>
        }
      />

      <section aria-label="Key metrics" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <StatCard label="Total applications" value={String(s?.total_applications ?? 0)} icon={<FileStack className="h-5 w-5" />} isLoading={loading} />
        <StatCard label="Verified" value={String(s?.verified ?? 0)} tone="success" icon={<CheckCircle2 className="h-5 w-5" />} isLoading={loading} />
        <StatCard label="Rejected" value={String(s?.rejected ?? 0)} tone="danger" icon={<XCircle className="h-5 w-5" />} isLoading={loading} />
        <StatCard label="Pending review" value={String(s?.needs_review ?? 0)} tone="warning" icon={<Clock3 className="h-5 w-5" />} isLoading={loading} />
        <StatCard
          label="Avg. confidence"
          value={formatPercent(s?.average_confidence, 1)}
          tone="info"
          hint="Across scored applications"
          icon={<Gauge className="h-5 w-5" />}
          isLoading={loading}
        />
        <StatCard
          label="Success rate"
          value={formatPercent(s?.success_rate, 1)}
          tone="brand"
          hint="Verified ÷ decided"
          icon={<TrendingUp className="h-5 w-5" />}
          isLoading={loading}
        />
      </section>

      <section className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-5">
        <Card className="xl:col-span-3">
          <CardHeader title="Verification volume" description="Daily outcomes over the last 14 days" />
          {loading || !s ? <Skeleton className="h-72 w-full" /> : <VolumeChart data={s.daily_volume} />}
        </Card>
        <Card className="xl:col-span-2">
          <CardHeader title="Status breakdown" description="Current distribution of applications" />
          {loading || !s ? <Skeleton className="h-72 w-full" /> : <StatusDonut data={s.status_breakdown} total={s.total_applications} />}
        </Card>
      </section>

      <section className="mt-6">
        <Card padded={false}>
          <CardHeader
            className="mb-0 px-5 pt-5 pb-3"
            title="Recent applications"
            description="Latest documents processed by the pipeline"
            action={
              <Link to={ROUTES.applications} className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:underline">
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            }
          />
          <div className="px-2 pb-2">
            {loading || !s ? (
              <div className="p-3">
                <SkeletonTable rows={6} cols={5} />
              </div>
            ) : (
              <RecentApplicationsTable rows={s.recent_applications} />
            )}
          </div>
        </Card>
      </section>
    </>
  );
}
