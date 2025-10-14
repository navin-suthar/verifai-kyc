import type { ApplicationStatus, ApplicationSummary, DashboardSummary, DocumentType } from '@/types/domain';

const NAMES = [
  'Rahul Sharma',
  'Priya Nair',
  'Aarav Mehta',
  'Ananya Iyer',
  'Vikram Rao',
  'Sneha Kulkarni',
  'Karan Malhotra',
  'Isha Banerjee',
  'Rohan Desai',
  'Meera Pillai',
  'Arjun Reddy',
  'Divya Menon',
];

const DOC_TYPES: DocumentType[] = [
  'synthetic_pan',
  'synthetic_national_id',
  'synthetic_passport',
  'synthetic_utility_bill',
];

const STATUS_CYCLE: ApplicationStatus[] = [
  'verified',
  'verified',
  'needs_review',
  'verified',
  'rejected',
  'verified',
  'needs_review',
  'pending',
  'verified',
  'rejected',
  'verified',
  'processing',
];

function isoDaysAgo(days: number, hourOffset = 0): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  d.setHours(9 + hourOffset, 15, 0, 0);
  return d.toISOString();
}

export const mockApplications: ApplicationSummary[] = NAMES.map((name, i) => {
  const status = STATUS_CYCLE[i % STATUS_CYCLE.length] ?? 'pending';
  const confidenceByStatus: Record<ApplicationStatus, number | null> = {
    verified: 91 + (i % 8),
    needs_review: 72 + (i % 15),
    rejected: 41 + (i % 25),
    pending: null,
    processing: null,
  };
  return {
    id: `app-${(1000 + i).toString(16)}`,
    customer_id: `DEMO-${10001 + i}`,
    applicant_name: name,
    document_type: DOC_TYPES[i % DOC_TYPES.length] ?? 'unknown',
    document_number_masked: `SYNTH••••${(1200 + i * 7).toString().slice(-4)}`,
    status,
    confidence: confidenceByStatus[status],
    created_at: isoDaysAgo(Math.floor(i / 2), i % 6),
    updated_at: isoDaysAgo(Math.floor(i / 2), (i % 6) + 1),
  };
});

export const mockDashboard: DashboardSummary = (() => {
  const count = (s: ApplicationStatus) => mockApplications.filter((a) => a.status === s).length;
  const scored = mockApplications.filter((a) => a.confidence !== null);
  const avg = scored.reduce((acc, a) => acc + (a.confidence ?? 0), 0) / Math.max(scored.length, 1);
  const decided = count('verified') + count('rejected');
  return {
    total_applications: mockApplications.length + 186,
    verified: count('verified') + 142,
    rejected: count('rejected') + 19,
    needs_review: count('needs_review') + 17,
    pending: count('pending') + count('processing') + 8,
    average_confidence: Math.round(avg * 10) / 10,
    success_rate: Math.round(((count('verified') + 142) / (decided + 161)) * 1000) / 10,
    status_breakdown: [
      { status: 'verified', count: count('verified') + 142 },
      { status: 'rejected', count: count('rejected') + 19 },
      { status: 'needs_review', count: count('needs_review') + 17 },
      { status: 'pending', count: count('pending') + count('processing') + 8 },
    ],
    daily_volume: Array.from({ length: 14 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (13 - i));
      const base = 8 + ((i * 7) % 9);
      return {
        date: d.toISOString().slice(0, 10),
        verified: base,
        rejected: 1 + ((i * 3) % 3),
        needs_review: 1 + ((i * 5) % 4),
      };
    }),
    recent_applications: mockApplications.slice(0, 8),
  };
})();
