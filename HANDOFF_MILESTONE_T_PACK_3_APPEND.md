
## Milestone T Pack 3 Handoff

### Completed

Historical Replay Runner & Research Dataset Builder is implemented as a research-only module.

### Verified Baseline

- Source baseline commit: `1aede17`
- Pack 3 focused tests: 16 passed
- Financial Naming: PASS
- Full regression after Pack 3: 2131 passed

### Architectural Decisions Preserved

- No TOP10 or TOP100 production ranking
- Research must pass governance before production visibility
- Historical replay must not see future candles
- One, two, or three position legs are optional research choices, not mandatory fixed stages
- Overnight holding does not automatically authorize a pyramid addition
- Capital survival and loss control remain higher-priority research objectives than maximum profit
- Research datasets are profile-independent and market-context classified
- All Pack 3 output remains `EXPERIMENTAL`

### Pack 3 Output

- deterministic chronological runner
- replay clock
- market snapshot provider interface
- research candidate provider interface
- append-only snapshot, candidate, decision, timeline, and summary datasets
- checksum chain verification
- tamper detection
- replay resume
- research dashboard metadata

### Not Yet Implemented

Pack 3 does not optimize entry, exit, stop placement, profit targets, holding duration, or pyramid additions. These belong to later Milestone T packs and must consume the Pack 3 datasets without weakening Research Quarantine.

### Recommended Next Pack

Milestone T Pack 4 — Exit, Loss-Control & Position Outcome Research Engine.

Recommended priorities:

1. capital survival and controlled loss
2. early invalidation and safe exit
3. partial exit and full exit alternatives
4. hold and trailing alternatives
5. missed-profit and avoided-loss measurement
6. post-exit M30/H1/H4/D1 observation
