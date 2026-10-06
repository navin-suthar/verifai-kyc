/**
 * Client-side input hygiene. React already escapes rendered text, so these
 * helpers focus on normalising what we *send* to the API. The backend
 * re-validates everything; this is defence in depth, not the only gate.
 */

const CONTROL_CHARS = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g;
const SCRIPT_TAG = /<\s*\/?\s*script[^>]*>/gi;

/** Trim, strip control characters and script tags, enforce a max length. */
export function sanitizeText(input: string, maxLength = 2000): string {
  return input.replace(CONTROL_CHARS, '').replace(SCRIPT_TAG, '').trim().slice(0, maxLength);
}

/** True when the string is empty or whitespace-only after sanitisation. */
export function isBlank(input: string | null | undefined): boolean {
  return !input || sanitizeText(input).length === 0;
}

/** Allow only http(s) and relative URLs in href attributes. */
export function isSafeHref(href: string): boolean {
  const trimmed = href.trim().toLowerCase();
  return trimmed.startsWith('/') || trimmed.startsWith('https://') || trimmed.startsWith('http://');
}

/** Basic identifier guard for path params (UUIDs / DEMO-xxxxx ids). */
export function isSafeIdentifier(id: string): boolean {
  return /^[A-Za-z0-9_-]{1,64}$/.test(id);
}

/** Validate that an object has all required keys present (not undefined). */
export function hasRequiredKeys<T extends object>(obj: unknown, keys: readonly (keyof T)[]): obj is T {
  if (typeof obj !== 'object' || obj === null) return false;
  return keys.every((k) => Object.prototype.hasOwnProperty.call(obj, k));
}
