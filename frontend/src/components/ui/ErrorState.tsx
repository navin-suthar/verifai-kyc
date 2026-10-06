import { AlertTriangle, RefreshCw } from 'lucide-react';
import Button from './Button';
import type { ApiError } from '@/lib/api/client';
import { cn } from '@/lib/utils/cn';

interface ErrorStateProps {
  error: ApiError | string;
  onRetry?: () => void;
  className?: string;
  compact?: boolean;
}

export default function ErrorState({ error, onRetry, className, compact = false }: ErrorStateProps) {
  const message = typeof error === 'string' ? error : error.message;
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center rounded-xl border border-danger/30 bg-danger-soft/40 text-center',
        compact ? 'px-4 py-6' : 'px-6 py-12',
        className,
      )}
    >
      <AlertTriangle className="mb-2 h-6 w-6 text-danger" aria-hidden="true" />
      <p className="text-sm font-medium text-fg">Something went wrong</p>
      <p className="mt-1 max-w-md text-sm text-fg-muted">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry} leftIcon={<RefreshCw className="h-3.5 w-3.5" />}>
          Try again
        </Button>
      )}
    </div>
  );
}
