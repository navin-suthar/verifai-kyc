# Document Requirements

This catalogue lists the synthetic documents accepted by VerifAI.

## Synthetic PAN

- Purpose: tax-style identity for the demo.
- Number format: `SYNTHETIC` followed by four digits, for example `SYNTHETIC1234`.
- Typical extracted fields: full name, date of birth, document number, address.

## Synthetic National ID

- Purpose: analogue of a national photo-ID. This is **not** Aadhaar.
- Number format: `DEMO-####-####-####`.
- The HTTP route `/api/verify/aadhaar` is a familiar name only. It calls the mock national-ID
  service and never contacts a government system.

## Synthetic Passport

- Purpose: travel-document analogue for higher-assurance demos.
- Number format: `SYNP` followed by seven digits, for example `SYNP1234567`.

## Synthetic Utility Bill

- Purpose: address supporting document.
- Number format: `ACC-DEMO-` followed by six digits.
- A utility bill alone is not enough to verify identity; it supports address verification.

## File types the platform accepts

- `.txt` and `.json` — preferred for local demos because extraction is deterministic.
- `.pdf` — text-based PDFs only.
- `.png` and `.jpg` — accepted for preview; machine-readable text may be missing without OCR.

Maximum size is configured by `MAX_UPLOAD_BYTES` (default 5 MB).
