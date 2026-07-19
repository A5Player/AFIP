
## Phase U Pack 3.3.3 — M30 Chronological Replay & Coverage Evidence

- Added deterministic per-timeframe replay coverage evidence.
- Replay checkpoints are now scoped to exact source-window identity.
- Legacy partial checkpoints are retained append-only but are not assumed to prove current-window coverage.
- M5 2,000/1,441 evidence indicates continuation from index 559 under the legacy ID; exact current-window coverage was not provable.
- M30 replay remains enabled through the universal timeframe registry.
- No live execution, risk, lot sizing, SL, TP, or capital policy change.
