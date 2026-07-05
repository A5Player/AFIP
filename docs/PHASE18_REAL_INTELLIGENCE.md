# AFIP Phase 18 — Real Intelligence Pack

This patch replaces placeholder-only behavior with a SIMULATION signal flow.

## Flow

Market Snapshot
→ Trend Intelligence
→ Momentum Intelligence
→ Volatility Intelligence
→ Liquidity Intelligence
→ Signal Score Calculator
→ Decision Service

## Safety

This patch does not place orders.
It only returns BUY / SELL / WAIT decisions in SIMULATION mode.

## Next

Phase 19 should connect the snapshot input to MarketDataProvider / MT5 data without enabling live execution.
