# Address Verification Rules

Address verification is required according to the uploaded KYC policy whenever an application
will be used to open a relationship that depends on a serviceable mailing address.

## When address verification is required

Address verification is required when:

- The identity document does not include a complete residential address.
- The extracted address is missing a postal code.
- The mock registry reports that the name matched but the address differs.
- The applicant is applying from a jurisdiction that the policy treats as address-sensitive.

A complete address in this demo must contain a street or locality **and** a 5 or 6 digit postal code.

## Why this application may require address verification

If an analyst asks why a specific application requires address verification, the usual reasons are:

- Rule ADDR-001 failed because the address is incomplete.
- The mock utility or national-ID service returned a partial match.
- Confidence fell into the human-review band, so a reviewer must confirm the address against a
  supplementary synthetic utility bill.

## Acceptable address evidence

Acceptable synthetic evidence includes:

- A Synthetic Utility Bill (account numbers look like ACC-DEMO-123456).
- An address block printed on a Synthetic Passport or Synthetic National ID.
- A reviewer note confirming a supplementary document was checked.

## What is not acceptable

Screenshots of real utility bills, bank statements, or government letters are not acceptable.
The platform will refuse payloads that look like real personal data.
