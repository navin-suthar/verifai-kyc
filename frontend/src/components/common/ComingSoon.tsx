import { Construction } from 'lucide-react';
import { Card, EmptyState, PageHeader } from '@/components/ui';

interface ComingSoonProps {
  title: string;
  description: string;
  phase: string;
}

/** Placeholder used while a feature is scheduled for a later build phase. */
export default function ComingSoon({ title, description, phase }: ComingSoonProps) {
  return (
    <>
      <PageHeader title={title} description={description} />
      <Card>
        <EmptyState
          icon={<Construction className="h-6 w-6" aria-hidden="true" />}
          title={`Scheduled for ${phase}`}
          description="This screen is part of the incremental build plan and will be wired up in a later phase."
        />
      </Card>
    </>
  );
}
