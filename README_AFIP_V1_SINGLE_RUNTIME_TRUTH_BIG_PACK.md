# AFIP V1 Single Runtime Truth Big Pack

Purpose: replace duplicated dashboard process/session/financial/runtime presentation calculations with one read-only authoritative runtime truth model.

## Layers

1. MT5 Process — terminal64.exe path is running or stopped.
2. Broker Session — connected only when verified by an explicit active diagnostic; passive mode never claims login/session verification.
3. Financial Evidence — LIVE, RECENT_SNAPSHOT, STALE_SNAPSHOT, or DATA_UNAVAILABLE.
4. AFIP Runtime — original AFIP runtime state.
5. Operational State — derived presentation state used consistently by Operations and Live MT5 dashboards.

## Safety

- Passive monitoring only.
- No MetaTrader5.initialize() from dashboard generation.
- No login, reconnect, terminal launch, order check, or order send.
- No changes to lot sizing, SL, TP, intelligence, risk, gateway, or execution policy.

## Expected example

When AFIP runtime says RUNNING but P3 terminal is closed:

- AFIP Runtime: RUNNING
- MT5 Process: STOPPED
- Broker Session: DISCONNECTED
- Operational State: DEGRADED
- Financial Evidence: snapshot-labelled, never LIVE

All dashboard pages consume the same contract fields.

## Runner repair

Passive MT5 observation is diagnostic. A non-zero checker exit code can mean that one or more configured terminal processes are intentionally stopped; it must not abort dashboard generation. The repaired runner records a warning and continues. Compile, focused regression, and dashboard-generation failures remain blocking.
