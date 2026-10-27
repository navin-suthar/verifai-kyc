# Mock Verification Policy

All external verification in VerifAI is **mocked**.

## What the mock service is

The mock service is a local FastAPI module that pretends to be a PAN registry, a national-ID
service, a passport authority or a utility provider. It returns realistic demo JSON such as:

```
{ "status": "verified", "matchScore": 96, "message": "Synthetic document successfully matched" }
```

Available routes:

- `POST /api/verify/pan`
- `POST /api/verify/aadhaar` (synthetic national ID — the name is only an analogue)
- `POST /api/verify/document`

## What the mock service is not

It is not a government API. It does not connect to NSDL, UIDAI, a credit bureau, or any bank.
Match scores are derived from a hash of the synthetic document number so demos are repeatable.

## How mock results affect decisions

- `verified` plus high confidence → automatic verification is allowed.
- `mismatch` → human review, even if confidence is high.
- `not_found` or `error` → human review or rejection depending on the confidence band.

The user interface must label every mock response as MOCK verification.
