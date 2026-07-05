# Production Batch 14.4 — Final Quality Fix

## Purpose
Fix the remaining local quality gate failures after Batch 14.3.

## Changes
- Add display-name compatibility for legacy quality labels that are still present in older intelligence files.
- Add provider compatibility in Real Market Data Intelligence Wiring for tests or providers that do not expose `connection_check`.

## Validation
Run:

```bash
python tools/afip_batch14_4_final_quality_fix.py
python tools/afip_local_quality_check.py
```

Expected:

```text
AFIP Local Quality Summary
Status: PASS
```
