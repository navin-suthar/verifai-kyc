import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { env } from '@/config/env';

/** Discriminated union so UI code can branch on error type without `any`. */
export type ApiError =
  | { type: 'network'; message: string }
  | { type: 'timeout'; message: string }
  | { type: 'unauthorized'; message: string }
  | { type: 'forbidden'; message: string }
  | { type: 'not_found'; message: string }
  | { type: 'validation'; message: string; fields?: Record<string, string> }
  | { type: 'rate_limited'; message: string; retryAfterSeconds?: number }
  | { type: 'server'; message: string; status: number }
  | { type: 'unknown'; message: string };

interface ErrorBody {
  detail?: unknown;
  message?: string;
}

function extractMessage(body: unknown, fallback: string): string {
  if (typeof body !== 'object' || body === null) return fallback;
  const b = body as ErrorBody;
  if (typeof b.message === 'string') return b.message;
  if (typeof b.detail === 'string') return b.detail;
  if (Array.isArray(b.detail)) {
    const first = b.detail[0] as { msg?: string } | undefined;
    if (first?.msg) return first.msg;
  }
  return fallback;
}

const API_ERROR_TYPES = new Set<ApiError['type']>([
  'network',
  'timeout',
  'unauthorized',
  'forbidden',
  'not_found',
  'validation',
  'rate_limited',
  'server',
  'unknown',
]);

export function isApiError(value: unknown): value is ApiError {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as { type?: unknown; message?: unknown };
  return typeof v.message === 'string' && typeof v.type === 'string' && API_ERROR_TYPES.has(v.type as ApiError['type']);
}

export function toApiError(error: unknown): ApiError {
  if (isApiError(error)) return error; // already normalised by the interceptor
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<unknown>;
    if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT') {
      return { type: 'timeout', message: 'The request timed out. Please try again.' };
    }
    if (!err.response) {
      return { type: 'network', message: 'Unable to reach the server. Check that the backend is running.' };
    }
    const { status, data, headers } = err.response;
    switch (status) {
      case 401:
        return { type: 'unauthorized', message: extractMessage(data, 'Please sign in to continue.') };
      case 403:
        return { type: 'forbidden', message: extractMessage(data, 'You do not have permission to do that.') };
      case 404:
        return { type: 'not_found', message: extractMessage(data, 'The requested resource was not found.') };
      case 400:
      case 413:
      case 415:
      case 422:
        return { type: 'validation', message: extractMessage(data, 'The request was invalid.') };
      case 429: {
        const retry = Number(headers?.['retry-after']);
        return {
          type: 'rate_limited',
          message: 'Too many requests. Please slow down.',
          retryAfterSeconds: Number.isFinite(retry) ? retry : undefined,
        };
      }
      default:
        if (status >= 500) {
          return { type: 'server', message: 'The server encountered an error. Please try again later.', status };
        }
        return { type: 'unknown', message: extractMessage(data, 'Something went wrong.') };
    }
  }
  if (error instanceof Error) return { type: 'unknown', message: error.message };
  return { type: 'unknown', message: 'Something went wrong.' };
}

type UnauthorizedHandler = () => void;
let onUnauthorized: UnauthorizedHandler | null = null;

/** Allows the auth provider to react to 401s (e.g. clear session, redirect). */
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  onUnauthorized = handler;
}

function createClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: env.apiBaseUrl,
    timeout: env.requestTimeoutMs,
    withCredentials: true, // session cookie is httpOnly; never readable by JS
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      Accept: 'application/json',
    },
    maxContentLength: 25 * 1024 * 1024,
  });

  instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    config.headers.set('X-Request-Id', crypto.randomUUID());
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    (error: unknown) => {
      const apiError = toApiError(error);
      if (apiError.type === 'unauthorized' && onUnauthorized) onUnauthorized();
      return Promise.reject(apiError);
    },
  );

  return instance;
}

export const apiClient = createClient();
