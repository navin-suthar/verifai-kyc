# Validation Rules

Every extracted application is evaluated by a deterministic rule engine before mock verification.

## REQ-001 Mandatory fields present

Name, date of birth and document number must all be extracted. Failure is an error and blocks
automatic verification.

## NAME-001 Applicant name format

The name must contain at least two words and only letters, spaces, apostrophes, periods or hyphens.

## DOB-001 Applicant age ≥ 18

The date of birth must parse as an ISO or common European date and the applicant must be 18 or older.
Future dates fail this rule.

## FMT-001 Document number format

The document number must match the synthetic pattern for the classified document type.
Real-world PAN and Aadhaar patterns fail this rule and the privacy guard.

## PII-001 No real-format identifiers

A privacy guard rejects any payload containing a real-format PAN (`ABCDE1234F` shape) or a
12-digit Aadhaar-like number. This rule exists so the portfolio demo cannot be misused.

## ADDR-001 Address completeness

Warning-level. The address should include a postal code. Failure routes the case to human review
instead of automatic rejection.

## TYPE-001 Recognised document type

The document must classify as Synthetic PAN, Synthetic National ID, Synthetic Passport or
Synthetic Utility Bill. Unknown types go to human review.

## How rules interact with thresholds

Error-level failures always prevent automatic verification.
If confidence is also below the investigation floor (`REVIEW_MIN_CONFIDENCE`, default 70),
the application is rejected for manual investigation.
If confidence is at or above that floor, the application is sent to human review.
