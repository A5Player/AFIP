# AFIP Handoff — Production Bring-up Pack 4

## Current Status

Production Bring-up Pack 4 has been prepared as an incremental patch on top of the attached AFIP.zip authoritative repository state.

Latest user baseline before this patch:

- GitHub commit: 8d045ac
- Production Bring-up Pack 3: completed and pushed
- pytest: 964 passed
- AFIP Local Quality Check: PASS
- Dashboard: PASS
- MT5: READY
- Windows VPS: READY
- Broker policy: XM only
- Symbol policy: GOLD# only
- Execution: LOCKED_SIMULATION_ONLY
- Live execution: DISABLED

## Production Bring-up Pack 4

Pack 4 adds Market Session and Trading Calendar Monitor integration.

### Added

- MarketCalendarRuntime
- MarketCalendarReport
- Market open / close detection
- Weekend detection for gold market closure window
- Configurable holiday detection
- Asia, London, and New York session flags
- Trading allowed flag
- Trading block reason
- Dashboard Live Market Status
- Next review time
- Read-only Market Calendar dashboard panel
- Dashboard Market panel now uses calendar telemetry
- Deterministic tests for READY, WAITING, HOLIDAY, WEEKEND, BLOCKED, and dashboard render states
- Documentation, file list, run scripts, and quality result file

## Safety Policy

- Live trading remains disabled.
- Trading logic changed: false.
- Version 1 remains XM + GOLD# only.
- Multi-broker remains disabled for Version 1.
- The Market Calendar Monitor is read-only dashboard telemetry and never sends orders.
- Trading permission is explanatory only and does not enable execution.

## Required Validation

Run on VPS:

```powershell
pytest tests/test_production_bringup_pack_4.py -v
if ($LASTEXITCODE -ne 0) { exit }

pytest
if ($LASTEXITCODE -ne 0) { exit }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit }

python -m afip.dashboard_ui

git add .
git commit -m "Production Bring-up Pack 4 Market Session Trading Calendar"
git push
```

## Next Step

After Pack 4 passes on VPS, continue to Production Bring-up Pack 5: Explainable Order Center.
