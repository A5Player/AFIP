# Milestone J Pack 9 — Portfolio Decision Engine

This incremental production patch combines Entry Validation, Exit Validation, fixed-unit capacity, portfolio exposure, and risk approval into one explainable portfolio decision context.

## Decisions

- ENTER
- HOLD
- PARTIAL_CLOSE
- MOVE_STOP_LOSS
- CHANGE_TAKE_PROFIT
- TRAIL_STOP
- EXIT
- WAIT

The engine remains read-only. It never sends, modifies, or closes a broker order. Version 1 remains XM-only and GOLD#-only. One Unit remains exactly 0.01 lot.
