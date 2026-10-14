import { useState, type FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Bot, FileSearch, Lock, ShieldCheck, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { toApiError } from '@/lib/api/client';
import { isBlank, sanitizeText } from '@/lib/security/sanitize';
import { env } from '@/config/env';
import { ROUTES } from '@/app/routes';

const DEMO_USERNAME = 'demo.analyst';
const DEMO_PASSWORD = 'demo-pass-2024';

const HIGHLIGHTS = [
  { icon: FileSearch, title: 'Document intelligence', text: 'Extract and score fields from synthetic KYC documents.' },
  { icon: ShieldCheck, title: 'Explainable decisions', text: 'Every outcome shows the rules, scores and evidence behind it.' },
  { icon: Bot, title: 'Grounded assistant', text: 'A local RAG assistant that cites the policy it answers from.' },
];

export default function LoginPage() {
  const { state, login } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState(DEMO_USERNAME);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const redirectTo = (location.state as { from?: string } | null)?.from ?? ROUTES.dashboard;

  if (state.status === 'authenticated') return <Navigate to={redirectTo} replace />;

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const cleanUser = sanitizeText(username, 64);
    const cleanPass = password.trim();
    if (isBlank(cleanUser) || isBlank(cleanPass)) {
      setFormError('Username and password are required.');
      return;
    }
    setFormError(null);
    setIsSubmitting(true);
    try {
      await login(cleanUser, cleanPass);
      toast({ title: 'Welcome back', description: 'Signed in to the demo workspace.', variant: 'success' });
      navigate(redirectTo, { replace: true });
    } catch (err) {
      const apiErr = toApiError(err);
      setFormError(apiErr.type === 'unauthorized' ? 'Invalid demo credentials.' : apiErr.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="relative hidden flex-col justify-between overflow-hidden bg-brand-900 p-12 text-white lg:flex">
        <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-brand-600/40 blur-3xl" aria-hidden="true" />
        <div className="absolute -right-24 -bottom-24 h-96 w-96 rounded-full bg-indigo-400/20 blur-3xl" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 ring-1 ring-white/20">
            <ShieldCheck className="h-6 w-6" aria-hidden="true" />
          </span>
          <div>
            <p className="text-lg font-semibold">{env.appName}</p>
            <p className="text-xs text-brand-200">KYC Document Intelligence &amp; Verification</p>
          </div>
        </div>
        <div className="relative max-w-md">
          <h2 className="text-3xl font-semibold leading-tight">
            AI-assisted KYC with a human in the loop.
          </h2>
          <p className="mt-3 text-sm text-brand-100/80">
            Local LLM, local vector search, local mock verification. Built to demonstrate production-style AI engineering
            without touching real personal data.
          </p>
          <ul className="mt-8 space-y-5">
            {HIGHLIGHTS.map((h) => (
              <li key={h.title} className="flex gap-3">
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <h.icon className="h-4 w-4" aria-hidden="true" />
                </span>
                <div>
                  <p className="text-sm font-medium">{h.title}</p>
                  <p className="text-xs text-brand-100/70">{h.text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-[11px] text-brand-200/70">
          Portfolio demo · Ollama + llama3.2-vision · Qdrant · FastAPI · PostgreSQL · React
        </p>
      </section>

      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white">
              <ShieldCheck className="h-6 w-6" aria-hidden="true" />
            </span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Sign in to the demo</h1>
          <p className="mt-1 text-sm text-fg-muted">Use the pre-filled demo credentials. No account is required.</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4" noValidate>
            <fieldset className="space-y-4" disabled={isSubmitting}>
              <div>
                <label htmlFor="username" className="mb-1.5 block text-sm font-medium">
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  maxLength={64}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="h-10 w-full rounded-lg border bg-surface px-3 text-sm text-fg placeholder:text-fg-subtle focus:border-brand-500"
                />
              </div>
              <div>
                <label htmlFor="password" className="mb-1.5 block text-sm font-medium">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  maxLength={128}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-10 w-full rounded-lg border bg-surface px-3 text-sm text-fg placeholder:text-fg-subtle focus:border-brand-500"
                />
              </div>
            </fieldset>

            {formError && (
              <p role="alert" className="rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-red-700 dark:text-red-300">
                {formError}
              </p>
            )}

            <Button type="submit" className="w-full" size="lg" isLoading={isSubmitting} leftIcon={<Lock className="h-4 w-4" />}>
              Enter demo workspace
            </Button>
          </form>

          <div className="mt-6 rounded-lg border bg-surface-2/60 p-3 text-xs text-fg-muted">
            <p className="flex items-center gap-1.5 font-medium text-fg">
              <Sparkles className="h-3.5 w-3.5 text-brand-500" aria-hidden="true" /> Privacy notice
            </p>
            <p className="mt-1">
              This application processes only synthetic documents. Do not upload real identity documents. Verification
              results come from a local mock service and have no legal meaning.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
