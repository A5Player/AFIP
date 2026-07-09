# Production Milestone H Pack 6 — Research Center

## Scope

Pack 6 adds the AFIP Research Center runtime. It separates Research statistics from Live statistics and prepares dashboard-ready Top 10 analytics for walk forward, paper trading, and standard learning.

## Added

- Research Center runtime
- Research Center report models
- Research-only ranking groups
- Live statistics separation policy
- Standard learning candidate gate
- Dashboard runtime dependency wiring
- Pack 6 tests
- Pack 6 run scripts

## Research Center Dashboard Groups

- Top 10 Trading Hours
- Top 10 Trading Sessions
- Top 10 Market Regimes
- Top 10 Entry Plans
- Top 10 Exit Plans
- Top 10 Patterns
- Top 10 Engine Combinations
- Top 10 Profit Reasons
- Top 10 Loss Reasons

## Standard Learning Policy

Every 100 completed Research orders can become a temporary standard candidate only when the analysis improves overall quality. Permanent standard promotion remains reserved for every 1000 completed orders.

## Production Policy

- Broker: XM only
- Symbol: GOLD# only
- Multi broker: disabled for Version 1
- Live trading: disabled
- Trading logic changed: no
