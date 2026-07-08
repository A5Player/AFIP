# Production Milestone G Pack 8 — Production Release Candidate

Pack G8 adds the final Release Candidate review layer for Milestone G.

This pack does not add a new AI engine, does not place orders, and does not change trading decision logic. It evaluates whether existing Milestone G evidence is ready for a controlled production release candidate.

## Scope

- Production Release Candidate observation contract
- Deterministic RC policy gate
- RC readiness profile
- RC report
- In-memory RC repository
- Runtime entry point
- Pack-level tests
- RUN scripts
- Project database update
- Handoff update

## Production rules

- Patch Only
- Production Quality Only
- Financial terminology only
- Market Regime before Signal
- Data First Architecture
- Knowledge First Architecture
- Runtime remains deterministic
- No live execution
- No unrelated refactor

## Validation

Expected validation after applying this patch:

```powershell
pytest tests/test_production_milestone_g_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
```
