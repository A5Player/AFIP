
## Milestone T Pack 3 — Historical Replay Runner & Research Dataset Builder

Status: IMPLEMENTED AND VALIDATED

### Purpose

Provide a deterministic research-only runner that walks historical market candles one bar at a time without future exposure and builds append-only experimental datasets for later entry, exit, position-management, loss-control, and pyramid research.

### Components

- `afip/historical_replay_research/runtime.py`
- `afip/historical_replay_research/__init__.py`
- `tests/test_milestone_t_pack_3_historical_replay_runner.py`

### Research Datasets

- snapshots
- candidates
- decisions
- timeline
- run summaries

Each dataset is JSONL, append-only, sequence-numbered, and protected by a previous-checksum chain. All generated research records use state `EXPERIMENTAL` and remain unavailable to Production Runtime.

### Replay Guarantees

- unique strictly increasing timestamps
- one-bar-at-a-time execution
- snapshot provider receives visible candles only
- no future candle is included in decision context
- deterministic replay clock
- resumable processing from the latest `BAR_PROCESSED` event
- dataset tampering is detectable

### Production Boundary

No MT5 order check, order send, position modification, production lot sizing, TP, SL, or trading-decision behavior is changed by this pack.

### Validation

- Focused tests: 16 passed
- Financial Naming: PASS
- Full regression: 2131 passed
