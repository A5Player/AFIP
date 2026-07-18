# AFIP Milestone S Cleanup Pack 4.1

Patch-only implementation of independent profile allocation and adaptive per-unit Risk-Reward protection.

Key rules:

- R means Risk-Reward Ratio (RR).
- Confidence caps units at 1 / 2 / 3; it never mandates all available units.
- P1–P3 may execute the same signal and entry independently.
- Unit protection roles are RR_NEAR, RR_CORE and RR_RUNNER.
- SL is selected from validated research, structure, ATR or realized volatility.
- TP is derived from stop distance and the selected RR target.
- Demo execution remains stopped after installation.
