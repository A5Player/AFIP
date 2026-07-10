# Milestone L Pack 3 — Paper Decision Ledger

Adds a deterministic ledger for every paper decision. The ledger records the approved action, independent trade plan, market/news context, confidence evidence, rejected alternatives, runtime versions, and outcome-tracking readiness.

Protected runners may be excluded from a new-entry ticket count only when protected, but they remain included in total exposure and risk. Traditional DCA and averaging down remain prohibited.

Safety remains mandatory: XM only, GOLD# only, 1 Unit = 0.01 lot, LOCKED_SIMULATION_ONLY, Direct Execution false, Live Execution disabled, and NO_ORDER_SENT.

## Validation

```powershell
pytest tests/test_milestone_l_pack_3.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
