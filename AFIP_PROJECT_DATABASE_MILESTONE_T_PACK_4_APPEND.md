
## Milestone T Pack 4 — Exit, Loss-Control & Position Outcome Research Engine

Status: PATCH DELIVERED

- Added research-only exit and loss-control policy evaluation.
- Added dynamic profit-target, stop-loss, break-even, trailing-stop, and maximum-holding alternatives.
- Added position lifecycle, exit alternative, position outcome, and exit quality append-only datasets.
- Added outcome classification, MFE/MAE, profit capture, missed profit, avoided loss, capital preservation, and exit quality metrics.
- Same-bar stop/target ambiguity uses a conservative stop-first assumption.
- All records remain `EXPERIMENTAL`, `production_usable=false`, and protected by Research Quarantine.
- No MT5 order, Production Runtime, position sizing, TP, SL, or trading logic changed.
