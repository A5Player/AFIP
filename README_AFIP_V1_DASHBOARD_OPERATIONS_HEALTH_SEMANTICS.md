# AFIP V1 Dashboard Operations Health & Evidence Semantics

Read-only dashboard completion patch.

## Adds

- Per-profile operations status and operating mode.
- System summary distinguishing `MONITORING_ONLY` from runtime failure.
- Explicit financial evidence semantics:
  - `NOT_COLLECTED`
  - `NOT_TRACKED`
  - `NOT_CONFIGURED`
  - `NOT_EVALUATED_RUNTIME_STOPPED`
- Market-closed decision semantics.
- No missing financial value is presented as zero.

## Safety

No trading logic, lot sizing, capital authority, SL/TP, routing, MT5 order check, or order send behavior is changed.
