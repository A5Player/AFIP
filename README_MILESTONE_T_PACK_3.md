# AFIP Milestone T Pack 3

## Historical Replay Runner & Research Dataset Builder

Milestone T Pack 3 adds a research-only runner that walks historical candles one bar at a time, exposes only current and prior data to research providers, and builds append-only datasets inside the experimental research boundary.

## Included

- Strict chronological historical replay runner
- Deterministic replay clock and progress metadata
- Visible-history-only market snapshot provider
- Research candidate provider interface
- Candidate normalization and validation
- Snapshot dataset
- Candidate dataset
- Decision dataset
- Replay timeline dataset
- Run summary dataset
- Append-only JSONL storage
- Dataset checksum chain and tamper detection
- Replay resume from the latest processed bar
- Quarantine and dashboard metadata
- All records default to `EXPERIMENTAL`
- Production visibility remains disabled

## Research Flow

```text
Historical Candles
        ↓
Chronological Replay
        ↓
Visible Candles Only
        ↓
Market Snapshot
        ↓
Research Candidates
        ↓
Decision Record
        ↓
Append-only Experimental Datasets
```

The runner does not optimize entries, exits, stop placement, profit targets, position holding, or pyramid additions in this pack. It creates the deterministic data foundation required for those later research packs.

## Safety Boundary

This pack:

- does not call MT5 order check or order send
- does not open, modify, or close positions
- does not change current lot sizing
- does not change TP or SL policy
- does not change production trading logic
- does not promote research into production knowledge
- does not allow Production Runtime to read experimental datasets

## Dataset Integrity

Each JSONL entry contains:

- dataset name
- record sequence
- previous chain checksum
- record payload
- current chain checksum

Any modification to a prior record breaks dataset verification. Resume reads the append-only replay timeline and continues from the next unprocessed bar.

## Validation

Run from the AFIP repository root:

```powershell
.\APPLY_MILESTONE_T_PACK_3_DOC_UPDATES.ps1
.\RUN_MILESTONE_T_PACK_3.ps1
```

Expected focused validation:

```text
16 passed
AFIP Financial Naming Validation: PASS
AFIP Local Quality Summary: PASS
```
