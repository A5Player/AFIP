# AFIP Phase 19 — Market Data Simulation Workflow

Connects deterministic market snapshots to the real simulation signal pipeline.

Flow:
Market Data Provider -> Market Snapshot -> Intelligence -> Score -> Decision

Safety:
- No MT5 connection
- No live orders
- SIMULATION only

Next:
- Add MT5 adapter interface
- Normalize tick/candle data
- Add broker-agnostic market data contract
