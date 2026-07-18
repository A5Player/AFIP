# AFIP Milestone S Pack 5.8 — Blind Forward Research Engine

## Purpose

Adds a deterministic, execution-neutral engine for evaluating configured TP, SL and time-exit candidates using only closed bars strictly after a research entry.

## Certified behavior

- Forward-only evaluation; entry-time or earlier bars are rejected.
- No-look-ahead chronological bar validation.
- Multiple TP, SL and time-exit candidates from external configuration.
- MAE, MFE, holding bars and holding seconds.
- Conservative same-bar resolution: SL first.
- Deterministic SHA-256 input hash and result ID.
- Append-only JSONL result storage with duplicate protection and manifest.
- Research eligibility and quarantine reasons.
- Shared profile-independent research dataset.
- Execution authority is permanently `NONE` in this pack.

## Apply

Copy the patch contents into the AFIP repository root, preserving directories.

## Validate

```powershell
.\RUN_MILESTONE_S_PACK_5_8.ps1
python tools/afip_local_quality_check.py
pytest
```

This pack does not enable MT5, demo execution, or live execution.
