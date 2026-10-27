import { useRef, useState, type DragEvent, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileJson, FileText, ShieldAlert, UploadCloud } from 'lucide-react';
import { Badge, Button, Card, CardHeader, PageHeader } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';
import { uploadApplication } from '@/lib/api/applicationsApi';
import { toApiError } from '@/lib/api/client';
import { formatBytes } from '@/lib/utils/format';
import { cn } from '@/lib/utils/cn';
import { ROUTES } from '@/app/routes';

const MAX_BYTES = 5 * 1024 * 1024;
const ALLOWED = ['.txt', '.json', '.pdf', '.png', '.jpg', '.jpeg'];

const SAMPLES = [
  { href: '/samples/rahul_sharma_synthetic_pan.txt', label: 'Verified PAN sample', icon: FileText },
  { href: '/samples/priya_nair_synthetic_national_id.json', label: 'National ID (JSON)', icon: FileJson },
  { href: '/samples/incomplete_address_review.txt', label: 'Needs-review passport', icon: FileText },
];

const STEPS = ['Uploading', 'Extracting fields', 'Running rules', 'Mock verification', 'Decisioning'];

export default function UploadPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [step, setStep] = useState(0);

  const assignFile = (next: File | null) => {
    if (!next) {
      setFile(null);
      return;
    }
    const ext = `.${next.name.split('.').pop()?.toLowerCase() ?? ''}`;
    if (!ALLOWED.includes(ext)) {
      setError(`File type ${ext || 'unknown'} is not allowed.`);
      return;
    }
    if (next.size > MAX_BYTES) {
      setError(`File exceeds the ${formatBytes(MAX_BYTES)} limit.`);
      return;
    }
    setError(null);
    setFile(next);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    assignFile(e.dataTransfer.files[0] ?? null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Choose a synthetic KYC document to continue.');
      return;
    }
    setIsSubmitting(true);
    setStep(0);
    const timer = window.setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 700);
    try {
      const result = await uploadApplication(file);
      toast({
        title: 'Document processed',
        description: `${result.customer_id} is ${result.status.replace('_', ' ')}.`,
        variant: 'success',
      });
      navigate(ROUTES.application(result.id));
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr.message);
      toast({ title: 'Upload failed', description: apiErr.message, variant: 'error' });
    } finally {
      window.clearInterval(timer);
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Upload document"
        description="Submit a synthetic KYC file. Real identity documents are rejected by a privacy guard."
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <form onSubmit={handleSubmit}>
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={cn(
                'flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors',
                isDragging ? 'border-brand-500 bg-brand-50/60 dark:bg-brand-900/20' : 'border-line bg-surface-2/40',
              )}
            >
              <UploadCloud className="h-10 w-10 text-brand-500" aria-hidden="true" />
              <p className="mt-3 text-sm font-medium">Drop a synthetic document here, or click to browse</p>
              <p className="mt-1 text-xs text-fg-muted">TXT, JSON, PDF, PNG or JPEG · max 5 MB</p>
              <input
                ref={inputRef}
                type="file"
                accept={ALLOWED.join(',')}
                className="sr-only"
                onChange={(e) => assignFile(e.target.files?.[0] ?? null)}
              />
            </div>

            {file && (
              <p className="mt-3 text-sm text-fg">
                Selected: <span className="font-medium">{file.name}</span>{' '}
                <span className="text-fg-muted">({formatBytes(file.size)})</span>
              </p>
            )}

            {error && (
              <p role="alert" className="mt-3 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm">
                {error}
              </p>
            )}

            {isSubmitting && (
              <ol className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
                {STEPS.map((label, i) => (
                  <li
                    key={label}
                    className={cn(
                      'rounded-lg px-2 py-2 text-center text-[11px] font-medium',
                      i <= step ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-200' : 'bg-surface-2 text-fg-subtle',
                    )}
                  >
                    {label}
                  </li>
                ))}
              </ol>
            )}

            <div className="mt-5 flex justify-end">
              <Button type="submit" isLoading={isSubmitting} leftIcon={<UploadCloud className="h-4 w-4" />}>
                Run KYC pipeline
              </Button>
            </div>
          </form>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader title="Sample files" description="Download a synthetic document, then upload it." />
            <ul className="space-y-2">
              {SAMPLES.map((s) => (
                <li key={s.href}>
                  <a
                    href={s.href}
                    download
                    className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm hover:bg-surface-2"
                  >
                    <s.icon className="h-4 w-4 text-brand-500" />
                    {s.label}
                  </a>
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <div className="flex items-start gap-2">
              <ShieldAlert className="mt-0.5 h-4 w-4 text-warning" />
              <div>
                <p className="text-sm font-semibold">Privacy disclaimer</p>
                <p className="mt-1 text-xs text-fg-muted">
                  Never upload real Aadhaar, PAN, passport or bank documents. A privacy guard rejects real-format
                  identifiers. Verification is <Badge tone="warning">MOCK</Badge> only.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
