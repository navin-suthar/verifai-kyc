import { apiClient } from './client';
import { sanitizeText } from '@/lib/security/sanitize';
import type { ChatAnswer } from '@/types/domain';

export async function askAssistant(question: string, applicationId?: string): Promise<ChatAnswer> {
  const payload: { question: string; application_id?: string } = {
    question: sanitizeText(question, 1000),
  };
  if (applicationId) payload.application_id = applicationId;
  const { data } = await apiClient.post<ChatAnswer>('/assistant/ask', payload, { timeout: 180_000 });
  return data;
}
