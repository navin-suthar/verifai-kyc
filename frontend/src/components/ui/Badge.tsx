import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils/cn';

export type BadgeTone = 'neutral' | 'success' | 'danger' | 'warning' | 'info' | 'brand';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  dot?: boolean;
}

const TONES: Record<BadgeTone, string> = {
  neutral: 'bg-surface-2 text-fg-muted',
  success: 'bg-success-soft text-green-700 dark:text-green-400',
  danger: 'bg-danger-soft text-red-700 dark:text-red-400',
  warning: 'bg-warning-soft text-amber-700 dark:text-amber-400',
  info: 'bg-info-soft text-blue-700 dark:text-blue-400',
  brand: 'bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300',
};

const DOTS: Record<BadgeTone, string> = {
  neutral: 'bg-fg-subtle',
  success: 'bg-success',
  danger: 'bg-danger',
  warning: 'bg-warning',
  info: 'bg-info',
  brand: 'bg-brand-500',
};

export default function Badge({ tone = 'neutral', dot = false, className, children, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap',
        TONES[tone],
        className,
      )}
      {...rest}
    >
      {dot && <span className={cn('h-1.5 w-1.5 rounded-full', DOTS[tone])} aria-hidden="true" />}
      {children}
    </span>
  );
}
