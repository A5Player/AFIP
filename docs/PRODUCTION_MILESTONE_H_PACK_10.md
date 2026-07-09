# Production Milestone H Pack 10 — Production Readiness and VPS Demo Workflow

Pack 10 completes Milestone H as a release-candidate workflow for Windows VPS deployment, historical data, walk forward, research, paper trading, demo trading readiness, and Dashboard monitoring.

## Scope

- Production Readiness Runtime
- Demo Trading Readiness without live execution
- VPS deployment step model
- Dashboard Production Readiness panel
- Safe workflow handoff
- Backward compatibility with existing Production Milestone F production readiness runtime

## Version 1 Policy

- XM only
- GOLD# only
- Multi broker disabled
- Live trading disabled
- Demo trading readiness only

## Recommended VPS Sequence

1. Deploy AFIP to Windows VPS.
2. Configure MT5 path and profile.
3. Download historical data.
4. Validate quality.
5. Run Walk Forward.
6. Run Research.
7. Run Paper Trading.
8. Run Demo Trading.
9. Do not enable Live Trading.

## Dashboard

Run:

```powershell
python -m afip.dashboard_ui
```

Output:

```text
runtime\dashboard\afip_dashboard.html
```

The dashboard includes the Production Readiness panel when the runtime is in Demo / Production Readiness mode.
