# AFIP Milestone T Pack 2

## Chronological Replay & Position Management Research Foundation

Milestone T Pack 2 adds an isolated research-only foundation for replaying historical candles in strict chronological order and studying position-management alternatives without future leakage.

### Included

- Strict chronological candle replay
- No-future-data decision context
- Flexible one-, two-, or three-leg research plans
- Short, medium, long, and dynamic leg roles
- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)
- Decision alternatives: hold, close, partial close, break-even, trailing, pyramid, and no-pyramid
- Dynamic pyramid research gate
- Total-risk ceiling enforcement
- Post-exit M30/H1/H4/D1 observation fields
- Deterministic checksums
- Research output defaults to `EXPERIMENTAL`

### Safety Boundary

This pack does not send MT5 orders, modify production positions, change lot sizing, change TP/SL policy, or change current production trading logic. Overnight holding alone never authorizes an additional position. A pyramid candidate must remain profitable, have reduced existing risk, retain supportive market structure and regime, and stay inside the maximum total-risk ceiling.

### Validation

```powershell
.\RUN_MILESTONE_T_PACK_2.ps1
```
