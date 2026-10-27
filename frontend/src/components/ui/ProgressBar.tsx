import { cn } from '@/lib/utils/cn';

interface ProgressBarProps {
  value: number; // 0..100
  label?: string;
  showValue?: boolean;
  size?: 'sm' | 'md';
  tone?: 'auto' | 'brand' | 'success' | 'warning' | 'danger';
  className?: string;
}

function autoTone(value: number): 'success' | 'warning' | 'danger' {
  if (value >= 90) return 'success';
  if (value >= 70) return 'warning';
  return 'danger';
}

const FILL: Record<'brand' | 'success' | 'warning' | 'danger', string> = {
  brand: 'bg-brand-500',
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
};

export default function ProgressBar({ value, label, showValue = true, size = 'md', tone = 'auto', className }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const resolvedTone = tone === 'auto' ? autoTone(clamped) : tone;
  return (
    <div className={cn('w-full', className)}>
      {(label || showValue) && (
        <div className="mb-1 flex items-center justify-between text-xs">
          {label && <span className="text-fg-muted">{label}</span>}
          {showValue && <span className="font-medium tabular-nums text-fg">{Math.round(clamped)}%</span>}
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={Math.round(clamped)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
        className={cn('w-full overflow-hidden rounded-full bg-surface-2', size === 'sm' ? 'h-1.5' : 'h-2')}
      >
        <div className={cn('h-full rounded-full transition-all duration-500', FILL[resolvedTone])} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
