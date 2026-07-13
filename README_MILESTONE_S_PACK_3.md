# Milestone S Pack 3 — MT5 Multi-Terminal Connection Manager

Adds isolated, read-only MT5 terminal health verification for P1–P4. Each profile is initialized sequentially with its own terminal path, login and server; the MT5 session is shut down after every check. The manager verifies terminal presence, authentication, account/server match, GOLD# selection, tick availability and terminal connectivity. It writes `runtime/profiles/pN/mt5_health.json` for dashboard consumption.

No order API is called. Execution remains `LOCKED_SIMULATION_ONLY`, direct execution false, live execution false and `NO_ORDER_SENT`.

Run:

```powershell
python tools/afip_mt5_multi_terminal_check.py --profiles P1 P4 --reconnect-attempts 2
python -m afip.dashboard_ui
```
