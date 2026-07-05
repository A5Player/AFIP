# AFIP Production Milestone B Pack 1 Fix

This patch corrects the Intelligence Score Fusion confidence normalization.

## Change

- Replaces total configured weight normalization with active weighted contribution normalization.
- Keeps backward compatibility.
- Keeps international financial terminology.
- No execution side effects.

## Validation

Run:

```powershell
pytest tests/test_production_milestone_b_pack_1.py
python tools/afip_local_quality_check.py
```
