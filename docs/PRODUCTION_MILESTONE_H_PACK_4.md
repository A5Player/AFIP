# Production Milestone H Pack 4 — Runtime Service Manager

## Objective

Add deterministic Windows VPS runtime infrastructure before dashboard UI. This pack prepares AFIP to observe runtime health, recovery flow, heartbeat, event history, and dashboard-ready runtime state without enabling live trading.

## Scope

- Runtime Service Manager
- Runtime Recovery Engine
- Runtime Event Logger
- Dashboard Runtime dependency integration
- VPS-ready runtime status data model
- Pack 4 tests and run scripts

## Production Policy

- Broker: XM only
- Symbol: GOLD# only
- Multi broker: disabled for Version 1
- Live trading: disabled
- Execution remains simulation or paper only

## Dashboard Explainability

Runtime decisions expose:

- Waiting reason
- Recovery reason
- Expected next action
- Heartbeat status
- Internet status
- MT5 status
- Broker status
- Runtime event history

## Recovery Flow

Internet loss:

1. Pause trading
2. Wait for internet
3. Recheck MT5
4. Recheck broker

MT5 loss:

1. Pause trading
2. Reconnect MT5
3. Validate broker
4. Resume runtime after validation

Broker issue:

1. Pause trading
2. Validate XM broker
3. Refresh connection status
4. Resume runtime after validation

## Test Command

```powershell
pytest tests/test_production_milestone_h_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
```
