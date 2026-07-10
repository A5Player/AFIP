# Milestone L Pack 2 — Paper Execution Session Monitor

Adds deterministic Paper Execution session certification after the Pack 1 foundation.

## Scope
- Paper account and market-session readiness
- Market-data freshness
- Spread and latency limits
- Clock synchronization
- Risk and audit readiness
- Independent Trade Plan requirement
- Traditional DCA and averaging down disabled
- XM only, GOLD# only, 1 Unit = 0.01 Lot
- LOCKED_SIMULATION_ONLY and NO_ORDER_SENT
- Dashboard explainability in English and Thai

This pack records observation readiness only. It does not transmit, modify, or close a broker order.

## Validation
```powershell
pytest tests/test_milestone_l_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
