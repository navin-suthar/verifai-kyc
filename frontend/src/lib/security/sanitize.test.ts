import { describe, expect, it } from 'vitest';
import { isBlank, isSafeHref, isSafeIdentifier, sanitizeText } from '@/lib/security/sanitize';
import { documentTypeLabel, formatPercent } from '@/lib/utils/format';

describe('sanitizeText', () => {
  it('trims, strips control characters and script tags, and enforces length', () => {
    expect(sanitizeText('  hello\u0000 <script>alert(1)</script> world  ')).toBe('hello alert(1) world');
    expect(sanitizeText('abcdefghij', 4)).toBe('abcd');
  });

  it('treats whitespace-only input as blank', () => {
    expect(isBlank('   ')).toBe(true);
    expect(isBlank('ok')).toBe(false);
  });

  it('only allows safe hrefs and identifiers', () => {
    expect(isSafeHref('/applications/1')).toBe(true);
    expect(isSafeHref('javascript:alert(1)')).toBe(false);
    expect(isSafeIdentifier('abc123')).toBe(true);
    expect(isSafeIdentifier('../etc/passwd')).toBe(false);
  });
});

describe('format helpers', () => {
  it('formats percents and document labels', () => {
    expect(formatPercent(94.2, 1)).toBe('94.2%');
    expect(formatPercent(null)).toBe('—');
    expect(documentTypeLabel('synthetic_pan')).toBe('Synthetic PAN');
  });
});
