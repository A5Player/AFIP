# AFIP Milestone S Pack 4.7

Backward-compatible capital allocation recovery patch.

## Fix
- Recognizes all supported allocation modes without fall-through:
  - `LEGACY_FIXED_UNIT`
  - `CAPITAL_TIER_TABLE`
  - `RESEARCH_FIXED_001`
- Keeps the approved Pack 4.6 P1/P2 capital tables.
- Restores compatibility diagnostic fields used by existing tests and operators.
- Does not weaken any execution safety gate.

## Validation
- `pytest tests/test_milestone_s_pack_4.py tests/test_milestone_s_pack_4_7.py` → 17 passed
- `pytest` → 1812 passed
