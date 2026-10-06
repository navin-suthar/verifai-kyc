import Badge, { type BadgeTone } from './Badge';
import type { ApplicationStatus } from '@/types/domain';
import { statusLabel } from '@/lib/utils/format';

const TONE_BY_STATUS: Record<ApplicationStatus, BadgeTone> = {
  verified: 'success',
  rejected: 'danger',
  needs_review: 'warning',
  pending: 'neutral',
  processing: 'info',
};

interface StatusBadgeProps {
  status: ApplicationStatus;
  className?: string;
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <Badge tone={TONE_BY_STATUS[status]} dot className={className}>
      {statusLabel(status)}
    </Badge>
  );
}
