## Phase U Final Integration

- Added bounded one-shot research orchestration.
- Collector timeout prevents indefinite MT5/provider blocking.
- Final status is recorded at `runtime/research/final_research_run.json`.
- Research-only; execution authority remains false.
- Push only after local validation and a successful one-shot runtime run.
