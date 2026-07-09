# Production Bring-up Pack 1 — VPS Health Monitor

## Purpose

Production Bring-up Pack 1 turns the Dashboard System panel from placeholder VPS values into observable VPS health telemetry.

This pack is operational telemetry only. It does not change trading logic, does not enable live execution, and remains compatible with the Version 1 policy:

- Broker: XM only
- Symbol: GOLD# only
- Live execution: disabled
- Multi broker: disabled for Version 1

## Added Runtime

`afip.vps_health_monitor.VPSHealthMonitorRuntime`

The runtime reports:

- Hostname
- Operating system
- Windows version
- CPU percent
- RAM percent
- Disk usage
- Disk free GB
- Uptime seconds
- Python version
- Health gate
- Thai dashboard message
- English dashboard message

## Dashboard Integration

`afip.dashboard_ui.runtime` now includes VPS health values in the Dashboard System panel:

- VPS Health
- VPS Reason
- Hostname
- Windows
- Python
- Uptime Seconds
- CPU
- RAM
- Disk

## Safety

Live execution remains disabled. If live execution is requested, the health monitor returns `BLOCKED` with reason:

`live_execution_blocked_for_vps_health_monitor`

## Verification

Run:

```powershell
pytest tests/test_production_bringup_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
