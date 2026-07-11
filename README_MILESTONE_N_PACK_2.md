# Milestone N Pack 2 — Adaptive Position Sizing

Adds deterministic, research-only adaptive position sizing. The runtime converts portfolio capital, risk budget, stop distance, margin capacity and confidence into a bounded recommendation of 0–3 independent 0.01-lot units. It never creates a broker request or transmits an order.

## Safety
- XM only
- GOLD# only
- 1 unit = 0.01 lot
- Maximum 3 units
- Independent Trade Plan required
- Protected Runner supported
- LOCKED_SIMULATION_ONLY
- NO_ORDER_SENT

## Validation
```powershell
pytest tests/test_milestone_n_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
