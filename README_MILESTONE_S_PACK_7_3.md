# AFIP Milestone S Pack 7.3 — Deterministic Position Capacity Formula

## Purpose

This patch replaces the long P1-P3 `capital_tiers` arrays in `config/four_profile_demo.json` with compact deterministic formulas. The runtime still receives the same legacy in-memory capital-tier table before the capital growth engine evaluates account balance.

## Runtime compatibility

- `allocation_mode` remains `CAPITAL_TIER_TABLE`.
- The capital growth engine is unchanged.
- Explicit legacy `capital_tiers` remain supported and take precedence when present.
- P4 remains `RESEARCH_FIXED_001`.
- No entry, confidence, TP, SL, spread, execution, or order-management rule is changed.

## Preserved capacity endpoints

- P1: 12 tiers, maximum `0.10 x 3`, final balance threshold `19,800`.
- P2: 102 tiers, maximum `1.00 x 3`, final balance threshold `1,545,300`.
- P3: 1,002 tiers, maximum `10.00 x 3`, final balance threshold `600,000`.

## Validation

Run:

```powershell
.\RUN_MILESTONE_S_PACK_7_3.ps1
python -m pytest -q
python tools/afip_local_quality_check.py
```
