# AFIP Milestone T Pack 9

## MT5 Historical Provider, Resumable Backfill, Decision Trace Wiring & Dashboard Data Contract Foundation

This patch adds a dependency-injected MT5 historical provider foundation without adding order execution.

### Scope
- broker symbol resolution for GOLD/XAUUSD, oil and exact symbols
- earliest-available to latest-closed-bar historical collection
- chunked and resumable backfill checkpoints
- append-only historical bars and provider run evidence
- research-standard influence in runtime decision traces
- dashboard two-page data contract
- deterministic Top 10 and expandable Top 100 research rankings

### Dashboard contract
1. Operations page: P1-P4 visible together, five-second refresh, plan/standard, win rate, drawdown, profit, balances, floating P/L, position care and reasons.
2. Intelligence page: manual refresh with scroll preservation, Top 10 visible and Top 100 expandable by pattern and situation; unshown records remain retained and counted.

### Safety
This package does not call MT5 order_send, does not grant execution permission and does not bypass risk, trading-cost, profile-capacity or execution gates.
