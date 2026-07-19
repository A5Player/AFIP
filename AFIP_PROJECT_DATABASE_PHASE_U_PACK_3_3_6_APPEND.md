
## Phase U Pack 3.3.6 — Research Consumer Integration & Operational Profile Execution Control

- Added independent `execution_enabled` and `research_enabled` profile controls.
- P1/P4 execution enabled; P2/P3 execution disabled while all four profiles remain enabled for research.
- Demo workers skip execution-disabled profiles.
- Demo gateway blocks execution-disabled profiles before MT5 access.
- Research collector retains all research-enabled profiles.
- M30 remains available to research consumers through the universal timeframe registry.
- Live trading policy, lot sizing, capital gating, maximum units, SL and TP were not changed.
