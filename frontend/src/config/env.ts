/**
 * Typed access to Vite environment variables. Only non-secret configuration
 * belongs here: anything in VITE_* is embedded in the client bundle.
 */
interface AppEnv {
  apiBaseUrl: string;
  useMocks: boolean;
  appName: string;
  requestTimeoutMs: number;
}

function readBool(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) return fallback;
  return value === 'true' || value === '1';
}

export const env: AppEnv = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '/api',
  useMocks: readBool(import.meta.env.VITE_USE_MOCKS, false),
  appName: import.meta.env.VITE_APP_NAME ?? 'VerifAI',
  requestTimeoutMs: Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS ?? 30_000),
};
