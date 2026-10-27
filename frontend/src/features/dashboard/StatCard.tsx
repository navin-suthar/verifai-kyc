import type { ReactNode } from 'react';
import { Card, Skeleton } from '@/components/ui';
import { cn } from '@/lib/utils/cn';

interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
  icon: ReactNode;
  tone?: 'brand' | 'success' | 'danger' | 'warning' | 'info';
  isLoading?: boolean;
}

const ICON_TONES = {
  brand: 'bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300',
  success: 'bg-success-soft text-green-700 dark:text-green-400',
  danger: 'bg-danger-soft text-red-700 dark:text-red-400',
  warning: 'bg-warning-soft text-amber-700 dark:text-amber-400',
  info: 'bg-info-soft text-blue-700 dark:text-blue-400',
} as const;

export default function StatCard({ label, value, hint, icon, tone = 'brand', isLoading = false }: StatCardProps) {
  return (
    <Card className="flex items-start gap-4">
      <span className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-lg', ICON_TONES[tone])}>{icon}</span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-fg-muted">{label}</p>
        {isLoading ? (
          <Skeleton className="mt-1.5 h-7 w-20" />
        ) : (
          <p className="mt-0.5 text-2xl font-semibold tabular-nums tracking-tight text-fg">{value}</p>
        )}
        {hint && !isLoading && <p className="mt-0.5 truncate text-xs text-fg-subtle">{hint}</p>}
      </div>
    </Card>
  );
}
