import { useState } from 'react';
import { Check, MessageSquareMore, X } from 'lucide-react';
import { Button, Textarea } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';
import { submitReview } from '@/lib/api/applicationsApi';
import { toApiError } from '@/lib/api/client';
import { sanitizeText } from '@/lib/security/sanitize';
import type { ApplicationDetail, ReviewDecision } from '@/types/domain';

interface ReviewActionsProps {
  application: ApplicationDetail;
  onUpdated: (next: ApplicationDetail) => void;
}

export default function ReviewActions({ application, onUpdated }: ReviewActionsProps) {
  const { toast } = useToast();
  const [notes, setNotes] = useState('');
  const [pending, setPending] = useState<ReviewDecision | null>(null);

  const locked = application.status !== 'needs_review' && application.status !== 'pending';

  const handle = async (decision: ReviewDecision) => {
    setPending(decision);
    try {
      const next = await submitReview(application.id, decision, sanitizeText(notes, 2000));
      onUpdated(next);
      toast({ title: 'Review recorded', description: `Decision: ${decision.replace('_', ' ')}.`, variant: 'success' });
    } catch (err) {
      toast({ title: 'Review failed', description: toApiError(err).message, variant: 'error' });
    } finally {
      setPending(null);
    }
  };

  if (locked) {
    return (
      <p className="text-xs text-fg-muted">
        This application is already {application.status.replace('_', ' ')}
        {application.review ? ` by ${application.review.reviewer}` : ''}.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <label htmlFor="review-notes" className="text-xs font-medium text-fg-muted">
        Reviewer notes
      </label>
      <Textarea
        id="review-notes"
        maxLength={2000}
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Optional note stored on the audit trail…"
      />
      <div className="flex flex-wrap gap-2">
        <Button
          variant="success"
          size="sm"
          isLoading={pending === 'approve'}
          disabled={pending !== null}
          leftIcon={<Check className="h-4 w-4" />}
          onClick={() => void handle('approve')}
        >
          Approve
        </Button>
        <Button
          variant="danger"
          size="sm"
          isLoading={pending === 'reject'}
          disabled={pending !== null}
          leftIcon={<X className="h-4 w-4" />}
          onClick={() => void handle('reject')}
        >
          Reject
        </Button>
        <Button
          variant="outline"
          size="sm"
          isLoading={pending === 'request_info'}
          disabled={pending !== null}
          leftIcon={<MessageSquareMore className="h-4 w-4" />}
          onClick={() => void handle('request_info')}
        >
          Request more information
        </Button>
      </div>
    </div>
  );
}
