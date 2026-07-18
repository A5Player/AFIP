
## Milestone T Pack 2 — Chronological Replay & Position Management Research Foundation

Status: Implemented and locally validated.

Capabilities:
- Strict chronological replay with no-future-data decision contexts.
- Flexible one-to-three-leg position-management research plans.
- MFE/MAE and final path outcome measurement.
- Decision alternatives for hold, close, partial close, break-even, trailing, pyramid, and no-pyramid.
- Dynamic pyramid research requires profit, reduced existing risk, supportive regime/structure/trend, and total-risk compliance.
- Overnight holding alone never authorizes a pyramid add.
- Research records remain EXPERIMENTAL and isolated from production execution.

Production impact:
- No production trading-logic change.
- No MT5 order send or position modification.
- No lot-size, TP, or SL change.
