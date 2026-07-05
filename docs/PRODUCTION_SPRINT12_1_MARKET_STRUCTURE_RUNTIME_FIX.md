# AFIP Production Sprint 12.1 — Market Structure Runtime Fix

## Status
PASS candidate

## Objective
Fix the Sprint 12 runtime ordering issue in the simulation CLI and keep the console output aligned with the AFIP Financial Naming Standard.

## Changes
- Moved Modular Intelligence result extraction before Market Structure Intelligence display.
- Added safe fallback for Market Structure Intelligence while it is initializing.
- Added financial display aliases for legacy class names that have not yet been physically refactored.
- Preserved locked simulation-only execution status.

## Validation
Run:

```bash
python tools/validate_financial_naming.py
python afip.py simulate
python afip.py mt5-check
```
