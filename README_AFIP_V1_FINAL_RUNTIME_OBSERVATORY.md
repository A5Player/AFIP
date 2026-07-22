# AFIP V1 Final Pack — Runtime Observatory & Historical Research Completion

This patch completes AFIP V1 historical loading/replay observability without adding execution authority.

## Delivered

- Single runtime progress authority: `runtime/research/runtime_observatory_status.json`
- Append-only live timeline: `runtime/research/runtime_observatory_timeline.jsonl`
- Per-bar replay heartbeat, index, timeframe, processed/total, percentage, speed, ETA and candle timestamp
- Explicit lifecycle states: RUNNING, WAITING, STALLED, COMPLETED, FAILED
- Dashboard 4 reads the actual runtime authority first
- Compact 1080p-oriented observatory layout
- Obsolete `Capital / 0.01` compatibility presentation removed
- Live execution remains disabled and requires explicit separate authorization

## Safety

The observatory is read-only with `execution_authority=false` and `order_send_called=false`. It does not initialize execution, arm live mode, or send MT5 orders.
