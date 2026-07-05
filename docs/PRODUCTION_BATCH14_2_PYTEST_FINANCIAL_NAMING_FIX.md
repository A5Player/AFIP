# Production Batch 14.2 — Pytest Financial Naming Import Fix

## Objective
Remove the final legacy test import path that still expected AIF-era naming exports.

## Changes
- Updated `tests/phase2/test_afip_intelligence_naming.py`
- The test now calls the official AFIP financial naming validator directly.
- No legacy `aif` imports remain in this test.

## Validation
Run:

```bash
python tools/afip_local_quality_check.py
```

Expected:

```text
AFIP Local Quality Summary
Status: PASS
```
