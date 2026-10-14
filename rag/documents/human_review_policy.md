# Human Review Policy

VerifAI is a human-in-the-loop system. The model proposes; a reviewer disposes when confidence
is uncertain.

## Configurable thresholds

Thresholds are environment variables, not hardcoded constants:

- `AUTO_VERIFY_MIN_CONFIDENCE` (default 90) — applications at or above this score may be
  verified automatically when every error-level rule passed and the mock registry matched.
- `REVIEW_MIN_CONFIDENCE` (default 70) — applications in the band between this value and the
  auto-verify threshold require a human reviewer.

Applications below the review minimum are treated as potential rejections that still need
manual investigation before any production-like onboarding would proceed.

## Reviewer actions

A reviewer may:

- **Approve** — convert the application to Verified and record a note.
- **Reject** — convert the application to Rejected and record a note.
- **Request more information** — keep the application in Needs Review and explain what is missing.

Every action is written to the append-only audit log with the reviewer identity and timestamp.

## When the assistant can explain a result

The Knowledge Assistant may explain a verification result using the case file (status, issues,
decision reason) plus these policy documents. It must not invent extra rules.
