
## Milestone T Pack 9 — MT5 Historical Provider, Resumable Backfill, Decision Trace Wiring & Dashboard Data Contract Foundation

Status: COMPLETE

Added:
- `afip.mt5_historical_integration`
- broker symbol resolution
- resumable historical backfill checkpoints
- provider run evidence and runtime decision traces
- dashboard research rankings

Dashboard architecture decision:
- Page 1 Operations: P1-P4 together without vertical scrolling as the design target; refresh every 5-10 seconds, default 5 seconds.
- Page 2 Intelligence/Engine: manual refresh, preserve scroll position, Top 10 visible and Top 100 expandable by graph pattern and market situation.
- All unshown research records remain stored; dashboard reports the count beyond Top 100.

Execution remains governed by existing safety gates. No order sender was added.
