import { Link, useParams } from 'react-router-dom';
import { ArrowRight, Bot, FileWarning, Shield } from 'lucide-react';
import {
  Badge,
  Card,
  CardHeader,
  ErrorState,
  LinkButton,
  PageHeader,
  ProgressBar,
  Skeleton,
  SkeletonText,
  StatusBadge,
} from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { documentPreviewUrl, getApplication } from '@/lib/api/applicationsApi';
import { formatBytes, formatDateTime } from '@/lib/utils/format';
import { ROUTES } from '@/app/routes';
import type { ApplicationDetail } from '@/types/domain';
import ReviewActions from './ReviewActions';
import { useState } from 'react';

export default function AnalysisPage() {
  const { id = '' } = useParams();
  const { data, error, isLoading, reload } = useAsync(() => getApplication(id), [id]);
  const [override, setOverride] = useState<ApplicationDetail | null>(null);
  const app = override ?? data;

  if (error && !app) {
    return (
      <>
        <PageHeader title="Document analysis" />
        <ErrorState error={error} onRetry={reload} />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title={app?.applicant_name ?? 'Document analysis'}
        description={app ? `${app.customer_id} · submitted ${formatDateTime(app.created_at)}` : 'Loading application…'}
        actions={
          app ? (
            <LinkButton to={ROUTES.applicationResult(app.id)} variant="outline" rightIcon={<ArrowRight className="h-4 w-4" />}>
              Verification result
            </LinkButton>
          ) : undefined
        }
      />

      {isLoading && !app ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Skeleton className="h-96" />
          <SkeletonText lines={12} />
        </div>
      ) : app ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <DocumentPane app={app} />
          <div className="space-y-4">
            <Card>
              <div className="mb-4 flex items-center justify-between">
                <CardHeader className="mb-0" title="Extracted fields" description="Rule-based extraction with per-field confidence" />
                {app.confidence !== null && <StatusBadge status={app.status} />}
              </div>
              <ul className="space-y-4">
                {app.fields.map((field) => (
                  <li key={field.name}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-medium text-fg-muted">{field.label}</p>
                        <p className="font-medium text-fg">{field.value ?? '—'}</p>
                      </div>
                      <Badge tone="neutral">{field.source}</Badge>
                    </div>
                    <ProgressBar value={field.confidence} size="sm" className="mt-1.5" />
                  </li>
                ))}
              </ul>
            </Card>

            <Card>
              <CardHeader title="Validation results" description="Deterministic policy rules" />
              <ul className="space-y-2">
                {app.validation.map((check) => (
                  <li key={check.rule_id} className="rounded-lg border px-3 py-2">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium">
                        {check.rule_id} · {check.name}
                      </p>
                      <Badge tone={check.passed ? 'success' : check.severity === 'warning' ? 'warning' : 'danger'}>
                        {check.passed ? 'Passed' : check.severity}
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-fg-muted">{check.message}</p>
                  </li>
                ))}
              </ul>
            </Card>

            <Card>
              <CardHeader
                title="Mock verification"
                description="Local registry simulation — not a government API"
                action={<Badge tone="warning">MOCK</Badge>}
              />
              {app.verification ? (
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="text-fg-muted">Provider:</span> {app.verification.provider}
                  </p>
                  <p>
                    <span className="text-fg-muted">Status:</span> {app.verification.status}
                  </p>
                  <ProgressBar label="Match score" value={app.verification.match_score} />
                  <p className="text-fg-muted">{app.verification.message}</p>
                </div>
              ) : (
                <p className="text-sm text-fg-muted">Verification has not run yet.</p>
              )}
            </Card>

            <Card>
              <CardHeader title="Detected issues" />
              {app.issues.length === 0 ? (
                <p className="text-sm text-fg-muted">No issues were raised by the rule engine.</p>
              ) : (
                <ul className="space-y-2">
                  {app.issues.map((issue) => (
                    <li key={issue} className="flex gap-2 text-sm">
                      <FileWarning className="mt-0.5 h-4 w-4 text-warning" />
                      {issue}
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card>
              <CardHeader
                title="AI explanation"
                description="Generated locally; falls back to a template if Ollama is offline"
                action={<Bot className="h-4 w-4 text-brand-500" />}
              />
              <p className="text-sm leading-relaxed text-fg-muted">{app.explanation ?? 'No explanation stored.'}</p>
            </Card>

            <Card>
              <CardHeader title="Human review" description={`Auto-verify ≥ ${app.thresholds.auto_verify_min}% · Review ≥ ${app.thresholds.review_min}%`} />
              <ReviewActions application={app} onUpdated={setOverride} />
            </Card>
          </div>
        </div>
      ) : null}
    </>
  );
}

function DocumentPane({ app }: { app: ApplicationDetail }) {
  const isImage = app.document?.mime_type.startsWith('image/');
  return (
    <Card className="h-fit">
      <CardHeader
        title="Document preview"
        description={app.document ? `${app.document.filename} · ${formatBytes(app.document.size_bytes)}` : 'No file stored'}
        action={
          <Link
            to={`${ROUTES.assistant}?applicationId=${encodeURIComponent(app.id)}&diagnose=1`}
            className="text-xs font-medium text-brand-600 hover:underline"
          >
            Ask assistant
          </Link>
        }
      />
      <div className="overflow-hidden rounded-lg border bg-surface-2">
        {isImage ? (
          <img src={documentPreviewUrl(app.id)} alt="Uploaded synthetic document preview" className="max-h-[36rem] w-full object-contain" />
        ) : (
          <pre className="max-h-[36rem] overflow-auto p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap">
            {app.document?.text_excerpt ?? 'No extracted text is available for preview.'}
          </pre>
        )}
      </div>
      <p className="mt-3 flex items-center gap-1.5 text-[11px] text-fg-subtle">
        <Shield className="h-3.5 w-3.5" />
        Synthetic document · identifiers are masked in lists and hashed at rest
      </p>
    </Card>
  );
}
