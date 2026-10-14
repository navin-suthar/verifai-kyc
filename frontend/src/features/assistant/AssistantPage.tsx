import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Bot, FileSearch, Send } from 'lucide-react';
import { Badge, Button, Card, EmptyState, PageHeader, ProgressBar, Skeleton, StatusBadge, Textarea } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';
import { useAsync } from '@/hooks/useAsync';
import { askAssistant } from '@/lib/api/assistantApi';
import { getApplication } from '@/lib/api/applicationsApi';
import { toApiError } from '@/lib/api/client';
import { isBlank, isSafeIdentifier, sanitizeText } from '@/lib/security/sanitize';
import { documentTypeLabel, formatPercent } from '@/lib/utils/format';
import { ROUTES } from '@/app/routes';
import type { ApplicationDetail, ChatAnswer } from '@/types/domain';

interface Turn {
  question: string;
  answer: ChatAnswer | null;
  error?: string;
}

const GENERAL_SUGGESTIONS = [
  'What documents are required for KYC?',
  'Why does this application require address verification?',
  'What validation rules were applied?',
  'Explain this verification result.',
  'Is verification performed against a real government API?',
];

function caseSuggestions(app: ApplicationDetail): string[] {
  const statusLabel = app.status.replaceAll('_', ' ');
  return [
    `Diagnose why application ${app.customer_id} is ${statusLabel}.`,
    'Which validation rules failed or warned on this case?',
    'How did confidence and thresholds affect this decision?',
    'What does the mock verification result mean for this application?',
    'What should a human reviewer check next?',
  ];
}

function defaultDiagnosisQuestion(app: ApplicationDetail): string {
  return (
    `Diagnose this KYC application (${app.customer_id}, ${app.applicant_name ?? 'unknown applicant'}). ` +
    `Status is ${app.status.replaceAll('_', ' ')}. Explain the issues, failed/warning rules, ` +
    `confidence versus thresholds, and the mock verification outcome. Cite the policy sources.`
  );
}

export default function AssistantPage() {
  const [params] = useSearchParams();
  const rawAppId = params.get('applicationId');
  const applicationId = rawAppId && isSafeIdentifier(rawAppId) ? rawAppId : undefined;
  const autoDiagnose = params.get('diagnose') !== '0';
  const { toast } = useToast();
  const [question, setQuestion] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const diagnosedRef = useRef<string | null>(null);

  const { data: linkedApp, isLoading: loadingApp } = useAsync(
    () => (applicationId ? getApplication(applicationId) : Promise.resolve(null)),
    [applicationId],
  );

  const suggestions = useMemo(
    () => (linkedApp ? caseSuggestions(linkedApp) : GENERAL_SUGGESTIONS),
    [linkedApp],
  );

  const lastUngrounded = useMemo(() => turns.some((t) => t.answer && !t.answer.grounded), [turns]);

  const ask = async (raw: string) => {
    const clean = sanitizeText(raw, 1000);
    if (isBlank(clean)) return;
    setQuestion('');
    setIsAsking(true);
    setTurns((prev) => [...prev, { question: clean, answer: null }]);
    try {
      const answer = await askAssistant(clean, applicationId);
      setTurns((prev) => prev.map((t, i) => (i === prev.length - 1 ? { ...t, answer } : t)));
    } catch (err) {
      const message = toApiError(err).message;
      setTurns((prev) => prev.map((t, i) => (i === prev.length - 1 ? { ...t, error: message } : t)));
      toast({ title: 'Assistant unavailable', description: message, variant: 'error' });
    } finally {
      setIsAsking(false);
    }
  };

  useEffect(() => {
    if (!linkedApp || !applicationId || !autoDiagnose) return;
    if (diagnosedRef.current === applicationId) return;
    diagnosedRef.current = applicationId;
    void ask(defaultDiagnosisQuestion(linkedApp));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [linkedApp?.id, applicationId, autoDiagnose]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void ask(question);
  };

  return (
    <>
      <PageHeader
        title="KYC Knowledge Assistant"
        description={
          linkedApp
            ? `Diagnosing ${linkedApp.customer_id}. Case facts are sent with every question; policy claims still need citations.`
            : 'Answers are retrieved from local policy documents and cited. The model is not allowed to invent policy.'
        }
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2 min-h-[32rem]">
          {turns.length === 0 ? (
            <EmptyState
              icon={<Bot className="h-6 w-6" />}
              title={linkedApp ? 'Preparing case diagnosis…' : 'Ask a grounded KYC question'}
              description={
                linkedApp
                  ? 'The linked application data will be sent so the assistant can explain issues and next steps.'
                  : 'Try a prompt below. If the answer is not in the knowledge base, the assistant will refuse.'
              }
            />
          ) : (
            <ol className="space-y-5">
              {turns.map((turn, idx) => (
                <li key={`${turn.question}-${idx}`}>
                  <p className="text-xs font-medium text-fg-subtle">You</p>
                  <p className="mt-1 rounded-lg bg-surface-2 px-3 py-2 text-sm">{turn.question}</p>
                  <p className="mt-3 text-xs font-medium text-fg-subtle">Assistant</p>
                  {turn.error && <p className="mt-1 text-sm text-danger">{turn.error}</p>}
                  {!turn.answer && !turn.error && (
                    <p className="mt-1 text-sm text-fg-muted">
                      {linkedApp ? 'Diagnosing case with policy sources…' : 'Retrieving policy excerpts…'}
                    </p>
                  )}
                  {turn.answer && (
                    <div className="mt-1">
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{turn.answer.answer}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <Badge tone={turn.answer.grounded ? 'success' : 'warning'}>
                          {turn.answer.grounded ? 'Grounded' : 'Not in knowledge base'}
                        </Badge>
                        <Badge tone="neutral">{turn.answer.model}</Badge>
                        <Badge tone="neutral">{turn.answer.latency_ms} ms</Badge>
                      </div>
                      {turn.answer.sources.length > 0 && (
                        <ul className="mt-3 space-y-2">
                          {turn.answer.sources.map((src) => (
                            <li key={src.chunk_id} className="rounded-lg border px-3 py-2">
                              <p className="text-xs font-semibold">
                                {src.document}
                                {src.section ? ` · ${src.section}` : ''}
                              </p>
                              <p className="mt-1 text-xs text-fg-muted">{src.excerpt}</p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ol>
          )}

          <form onSubmit={handleSubmit} className="mt-6 flex items-end gap-2">
            <label htmlFor="assistant-q" className="sr-only">
              Question
            </label>
            <Textarea
              id="assistant-q"
              rows={2}
              maxLength={1000}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={
                linkedApp
                  ? 'Ask a follow-up about this application’s issues…'
                  : 'Ask about KYC policy, validation rules, or this application…'
              }
              className="min-h-[3rem]"
            />
            <Button type="submit" isLoading={isAsking} leftIcon={<Send className="h-4 w-4" />}>
              Ask
            </Button>
          </form>
        </Card>

        <div className="space-y-4">
          {applicationId && (
            <Card>
              <div className="mb-3 flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold">Linked case</p>
                  <p className="mt-0.5 text-xs text-fg-muted">Sent with every assistant question</p>
                </div>
                {linkedApp && <StatusBadge status={linkedApp.status} />}
              </div>
              {loadingApp && !linkedApp ? (
                <Skeleton className="h-28 w-full" />
              ) : linkedApp ? (
                <div className="space-y-3 text-sm">
                  <div>
                    <p className="font-medium">{linkedApp.applicant_name ?? 'Unknown applicant'}</p>
                    <p className="font-mono text-xs text-fg-subtle">{linkedApp.customer_id}</p>
                    <p className="mt-1 text-xs text-fg-muted">{documentTypeLabel(linkedApp.document_type)}</p>
                  </div>
                  {linkedApp.confidence !== null && (
                    <ProgressBar label="Overall confidence" value={linkedApp.confidence} size="sm" />
                  )}
                  <div>
                    <p className="text-xs font-medium text-fg-muted">Detected issues</p>
                    {linkedApp.issues.length === 0 ? (
                      <p className="mt-1 text-xs text-fg-subtle">No issues recorded.</p>
                    ) : (
                      <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-fg-muted">
                        {linkedApp.issues.map((issue) => (
                          <li key={issue}>{issue}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="rounded-lg border border-warning/30 bg-warning-soft/40 px-3 py-2 text-[11px] text-fg-muted">
                    Thresholds: auto-verify ≥ {linkedApp.thresholds.auto_verify_min}% · review ≥{' '}
                    {linkedApp.thresholds.review_min}% · mock verification{' '}
                    {linkedApp.verification
                      ? `${linkedApp.verification.status} (${formatPercent(linkedApp.verification.match_score, 0)})`
                      : 'n/a'}
                  </div>
                  <Link
                    to={ROUTES.application(linkedApp.id)}
                    className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:underline"
                  >
                    <FileSearch className="h-3.5 w-3.5" />
                    Back to analysis
                  </Link>
                </div>
              ) : (
                <p className="text-xs text-fg-muted">Could not load application {applicationId}.</p>
              )}
            </Card>
          )}

          <Card>
            <p className="text-sm font-semibold">{linkedApp ? 'Case questions' : 'Suggested questions'}</p>
            <ul className="mt-3 space-y-2">
              {suggestions.map((s) => (
                <li key={s}>
                  <button
                    type="button"
                    disabled={isAsking}
                    onClick={() => void ask(s)}
                    className="w-full rounded-lg border px-3 py-2 text-left text-xs hover:bg-surface-2 disabled:opacity-60"
                  >
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          </Card>

          {lastUngrounded && (
            <Card>
              <p className="text-xs text-fg-muted">
                At least one answer was refused because it was not present in the policy knowledge base. That is intentional.
              </p>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
