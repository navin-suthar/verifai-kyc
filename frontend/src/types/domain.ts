export type ApplicationStatus = 'pending' | 'processing' | 'verified' | 'rejected' | 'needs_review';

export const APPLICATION_STATUSES: readonly ApplicationStatus[] = [
  'pending',
  'processing',
  'verified',
  'rejected',
  'needs_review',
] as const;

export type DocumentType =
  | 'synthetic_pan'
  | 'synthetic_national_id'
  | 'synthetic_passport'
  | 'synthetic_utility_bill'
  | 'unknown';

export type FieldSource = 'rule' | 'ocr' | 'llm' | 'manual';

export type Severity = 'info' | 'warning' | 'error';

export type ReviewDecision = 'approve' | 'reject' | 'request_info';

export type VerificationStatus = 'verified' | 'not_found' | 'mismatch' | 'error' | 'skipped';

export interface ExtractedField {
  name: string;
  label: string;
  value: string | null;
  confidence: number; // 0..100
  source: FieldSource;
}

export interface ValidationCheck {
  rule_id: string;
  name: string;
  passed: boolean;
  severity: Severity;
  message: string;
}

export interface MockVerificationResult {
  provider: string;
  status: VerificationStatus;
  match_score: number; // 0..100
  message: string;
  is_mock: true;
  checked_at: string;
}

export interface ReviewRecord {
  id: string;
  decision: ReviewDecision;
  reviewer: string;
  notes: string | null;
  created_at: string;
}

export interface DecisionThresholds {
  auto_verify_min: number;
  review_min: number;
}

export interface ApplicationSummary {
  id: string;
  customer_id: string;
  applicant_name: string | null;
  document_type: DocumentType;
  document_number_masked: string | null;
  status: ApplicationStatus;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  preview_url: string | null;
  text_excerpt: string | null;
}

export interface ApplicationDetail extends ApplicationSummary {
  fields: ExtractedField[];
  validation: ValidationCheck[];
  verification: MockVerificationResult | null;
  issues: string[];
  explanation: string | null;
  decision_reason: string | null;
  document: DocumentInfo | null;
  review: ReviewRecord | null;
  thresholds: DecisionThresholds;
}

export interface StatusCount {
  status: ApplicationStatus;
  count: number;
}

export interface DailyVolume {
  date: string; // YYYY-MM-DD
  verified: number;
  rejected: number;
  needs_review: number;
}

export interface DashboardSummary {
  total_applications: number;
  verified: number;
  rejected: number;
  needs_review: number;
  pending: number;
  average_confidence: number;
  success_rate: number; // 0..100
  status_breakdown: StatusCount[];
  daily_volume: DailyVolume[];
  recent_applications: ApplicationSummary[];
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
}

export interface ChatSource {
  document: string;
  section: string | null;
  chunk_id: string;
  score: number;
  excerpt: string;
}

export interface ChatAnswer {
  answer: string;
  sources: ChatSource[];
  grounded: boolean;
  model: string;
  latency_ms: number;
}

export interface CurrentUser {
  username: string;
  role: 'analyst' | 'reviewer' | 'admin';
  display_name: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface TypeCount {
  document_type: string;
  count: number;
}

export interface ConfidenceByStatus {
  status: string;
  average_confidence: number;
  count: number;
}

export interface AnalyticsSummary {
  total_applications: number;
  verified: number;
  rejected: number;
  needs_review: number;
  pending: number;
  average_confidence: number;
  success_rate: number;
  auto_verified_share: number;
  human_reviewed: number;
  status_breakdown: StatusCount[];
  daily_volume: DailyVolume[];
  document_types: TypeCount[];
  confidence_by_status: ConfidenceByStatus[];
  thresholds: DecisionThresholds;
}

export interface PublicSettings {
  app_name: string;
  auto_verify_min_confidence: number;
  review_min_confidence: number;
  max_upload_bytes: number;
  allowed_extensions: string[];
  llm_enabled: boolean;
  ollama_model: string;
  mock_verification: boolean;
  privacy_notice: string;
}

export interface AssistantAskRequest {
  question: string;
  application_id?: string;
}
