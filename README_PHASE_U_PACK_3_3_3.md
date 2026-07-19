# AFIP Phase U Pack 3.3.3 — M30 Chronological Replay & Coverage Evidence

## Scope

- Preserves M30 chronological replay through the universal timeframe registry.
- Adds per-timeframe replay coverage evidence to `automatic_research_status.json`.
- Binds replay checkpoints to an exact immutable source-window identity.
- Prevents legacy checkpoint offsets from being assumed to cover a moving fixed-size MT5 window.
- Continues an existing checkpoint only when the exact window identity matches.
- Keeps research storage append-only and deterministic.
- Does not change live trading, risk, lot sizing, SL, TP, capital gating, or order execution.

## M5 2,000 → 1,441 investigation

The prior result is consistent with a legacy replay checkpoint whose next index was 559, leaving 1,441 bars in a 2,000-bar invocation. However, the legacy replay ID did not encode the source window boundaries, so the runtime could not prove that those 559 earlier events covered the same current MT5 window.

Pack 3.3.3 therefore does not treat a legacy partial checkpoint as verified coverage. It creates an exact-window generation ID and replays that window from index zero. Subsequent continuation is permitted only for the same timeframe, bar count, first timestamp, and last timestamp.

## Validation

Run:

```powershell
.\RUN_PHASE_U_PACK_3_3_3.ps1
```
