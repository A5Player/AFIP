# Production Milestone E Pack 5 — Dynamic Weight Engine

## Purpose

Pack 5 adds a deterministic Dynamic Weight Engine for AFIP. It converts regime-first intelligence contribution observations into data-derived adaptive weight profiles.

## Scope

- Dynamic weight observation normalization
- Market-regime-first intelligence grouping
- Data-derived normalized weight scoring
- Conflict-aware readiness checks
- Deterministic strongest-profile selection
- Production runtime wrapper

## Quality

- Pack test: `pytest tests/test_production_milestone_e_pack_5.py -v`
- Full pytest: PASS
- Local quality check: PASS
- Financial naming: PASS

## Architecture Rules

- Financial terminology only
- Market Regime before intelligence weighting
- Data First Architecture
- Knowledge First Architecture
- Deterministic runtime
- No hardcoded values when learnable
- Patch only
