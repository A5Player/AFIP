# AFIP Runtime State Architecture — RSA-2.1

## Purpose

Resolve the five manual-review blockers reported by RSA-2 using explicit,
reviewed classifications.

## Safety

This pack writes reports only. It does not move, delete, restore, archive,
untrack, stage, commit, or change `.gitignore`.

## Resolution summary

- RSA source documentation, tests and tools → `PERSISTENT_KNOWLEDGE`
- `capital_binding_verification.json` → `CERTIFICATION_EVIDENCE`
- Legacy replay-throughput ZIP → `PRODUCTION_EVIDENCE`

All recommended Git/archive actions remain manual and are deferred to RSA-3.
