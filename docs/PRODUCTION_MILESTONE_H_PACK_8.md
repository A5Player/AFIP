# Production Milestone H Pack 8 — Visible Dashboard UI Launcher

## Scope

Pack 8 adds the first visible AFIP Dashboard UI generated from existing runtime data.
It is a presentation layer only and does not change trading logic.

## Included

- Dashboard UI runtime
- HTML dashboard renderer
- Dashboard launcher
- Runtime, Intelligence, Trading, Analytics, AFIP Bank, Research, System, Market, and Order Center panels
- Thai and English panel descriptions
- Paper Trading and AFIP Bank visibility
- No Black Box explainability rows for order holding, risk, and next action

## Safety

- Live execution remains disabled
- Version 1 policy remains XM only and GOLD# only
- Multi broker remains disabled
- Dashboard UI blocks unsupported broker, symbol, or live mode

## Launch

```powershell
python -m afip.dashboard_ui
```

The generated file is:

```text
runtime/dashboard/afip_dashboard.html
```
