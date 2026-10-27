# KYC Policy Document

This document describes the Know Your Customer (KYC) policy for the VerifAI **synthetic demo platform**.
It is not a real regulatory filing and must not be used to process genuine identity documents.

## Purpose

KYC exists so a financial institution can establish who an applicant is, whether they are an adult,
and whether the documents they present are internally consistent before an account is opened.

In this demo, every applicant, address and identifier is invented. Verification calls are answered
by a local mock service. Outcomes have no legal meaning.

## Required evidence

A complete KYC application in this platform requires:

1. A government-style **synthetic identity document** (Synthetic PAN, Synthetic National ID, or Synthetic Passport).
2. Proof of **residential address** when the identity document does not already contain a full address.
3. An extracted **date of birth** showing the applicant is at least 18 years old.
4. A **document number** that matches the published synthetic format for that document type.

## Decision outcomes

The platform produces one of three outcomes:

- **Verified** — extraction confidence is at or above the auto-verify threshold, every error-level
  validation rule passed, and the mock registry returned a match.
- **Needs Human Review** — confidence is in the review band, a warning-level rule failed, or the
  mock registry returned only a partial match.
- **Rejected** — confidence is below the investigation floor or mandatory checks failed.

## Privacy rule

Real PAN numbers (five letters, four digits, one letter) and 12-digit Aadhaar-like numbers are
rejected at upload time. Operators must never upload scans of real identity documents.
