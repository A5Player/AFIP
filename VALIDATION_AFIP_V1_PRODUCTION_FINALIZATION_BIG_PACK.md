# Validation

Targeted regression verified during pack build:

- Production runtime authority
- P1-P4 unified execution contract
- PID-aware routing lock recovery
- Process-isolated sequential router
- Exact account/server/terminal ownership checks
- Capital tier and position ceiling contract alignment
- Phase U operational contract alignment

Result: `76 passed`

Full repository regression and Windows MT5 integration must be run on the user's VPS because MetaTrader5 terminals and credentials are not available in the pack build environment.
