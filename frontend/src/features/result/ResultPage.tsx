import { Link, useParams } from 'react-router-dom';
import { BadgeCheck, CircleAlert, Scale, Shield } from 'lucide-react';
import { Badge, Card, CardHeader, ErrorState, LinkButton, PageHeader, ProgressBar, Skeleton, StatusBadge } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { getApplication } from '@/lib/api/applicationsApi';
import { formatDateTime, formatPercent } from '@/lib/utils/format';
import { ROUTES } from '@/app/routes';
import ReviewActions from '@/features/analysis/ReviewActions';
import { useState } from 'react';
import type { ApplicationDetail } from '@/types/domain';

export default function ResultPage() {
  const { id = '' } = useParams();
  const { data, error, isLoading, reload } = useAsync(() => getApplication(id), [id]);
  const [override, setOverride] = useState<ApplicationDetail | null>(null);
  const app = override ?? data;

  if (error && !app) {
    return (
      <>
        <PageHeader title="Verification result" />
        <ErrorState error={error} onRetry={reload} />
      </>
    );
  }

  if (isLoading && !app) return <Skeleton className="h-80" />;
  if (!app) return null;

  return (
    <>
      <PageHeader
        title="Verification result"
        description={`${app.customer_id} · ${app.applicant_name ?? 'Unknown applicant'}`}
        actions={
          <LinkButton to={ROUTES.application(app.id)} variant="outline">
            Back to analysis
          </LinkButton>
        }
      />

      <Card className="mb-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-medium tracking-wide text-fg-subtle uppercase">Final decision</p>
            <div className="mt-2 flex items-center gap-3">
              <StatusBadge status={app.status} />
              <span className="text-sm text-fg-muted">Overall confidence {formatPercent(app.confidence, 1)}</span>
            </div>
            <p className="mt-3 max-w-2xl text-sm text-fg">{app.decision_reason}</p>
          </div>
          {app.confidence !== null && (
            <div className="w-full sm:w-56">
              <ProgressBar label="Confidence" value={app.confidence} />
            </div>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader title="Evidence" description="Why this outcome was produced" action={<Scale className="h-4 w-4 text-brand-500" />} />
          <ol className="space-y-3 text-sm">
            <li className="flex gap-2">
              <BadgeCheck className="mt-0.5 h-4 w-4 text-success" />
              Extracted {app.fields.filter((f) => f.value).length} of {app.fields.length} fields.
            </li>
            <li className="flex gap-2">
              <CircleAlert className="mt-0.5 h-4 w-4 text-warning" />
              {app.validation.filter((v) => !v.passed).length} validation issue(s) · {app.validation.filter((v) => v.passed).length} passed.
            </li>
            <li className="flex gap-2">
              <Shield className="mt-0.5 h-4 w-4 text-brand-500" />
              Mock verification: {app.verification?.status ?? 'skipped'} ({app.verification?.provider ?? 'n/a'})
              <Badge tone="warning">MOCK</Badge>
            </li>
          </ol>
        </Card>

        <Card>
          <CardHeader title="Thresholds" description="Configurable human-in-the-loop bands" />
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-fg-muted">Auto-verify</span>
              <span className="font-medium">≥ {app.thresholds.auto_verify_min}%</span>
            </li>
            <li className="flex justify-between">
              <span className="text-fg-muted">Human review</span>
              <span className="font-medium">
                {app.thresholds.review_min}–{app.thresholds.auto_verify_min - 1}%
              </span>
            </li>
            <li className="flex justify-between">
              <span className="text-fg-muted">Investigate / reject</span>
              <span className="font-medium">&lt; {app.thresholds.review_min}%</span>
            </li>
          </ul>
        </Card>

        <Card>
          <CardHeader title="Ask the assistant" />
          <p className="text-sm text-fg-muted">
            Grounded answers from the KYC policy knowledge base, with citations.
          </p>
          <Link
            to={`${ROUTES.assistant}?applicationId=${encodeURIComponent(app.id)}&diagnose=1`}
            className="mt-3 inline-flex text-sm font-medium text-brand-600 hover:underline"
          >
            Why was this document {app.status.replace('_', ' ')}?
          </Link>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader title="AI explanation" />
        <p className="text-sm leading-relaxed text-fg-muted">{app.explanation}</p>
        <p className="mt-4 text-xs text-fg-subtle">Recorded {formatDateTime(app.updated_at)}</p>
      </Card>

      <Card className="mt-4">
        <CardHeader title="Human review" />
        <ReviewActions application={app} onUpdated={setOverride} />
      </Card>
    </>
  );
}
