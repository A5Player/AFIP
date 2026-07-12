# Milestone R Pack 11 — Release Candidate Preparation

This patch adds a deterministic, immutable Release Candidate preparation layer.

It requires a valid Milestone R Pack 10 Production Certification and complete artifact, validation, and bilingual documentation manifests. Passing this pack prepares the repository for Release Candidate review only. It does not grant Release Candidate or Version 1.0 Final status and does not unlock execution.

Permanent controls remain unchanged: XM only, GOLD# only, 1 Unit = 0.01 lot, `LOCKED_SIMULATION_ONLY`, direct execution disabled, live execution disabled, and `NO_ORDER_SENT`.

## Validation

```powershell
pytest tests/test_milestone_r_pack_11.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
