# AFIP Milestone T Pack 4

## Exit, Loss-Control & Position Outcome Research Engine

Milestone T Pack 4 adds a research-only engine for evaluating hypothetical exit and position-management policies against chronological replay candles. Every result remains `EXPERIMENTAL`, append-only, and quarantined from Production Runtime.

## Included

- Exit Research Engine
- Loss-Control Research
- Dynamic profit-target research
- Dynamic stop-loss research
- Break-even research
- Trailing-stop research
- Maximum holding-period research
- Position lifecycle records
- Position outcome classification
- Exit quality scoring
- Capital preservation scoring
- MFE / MAE outcome metrics
- Profit capture, missed profit, and avoided loss metrics
- Multiple-policy experiment runner
- Expanded append-only research datasets
- Research Quarantine metadata

## Research Datasets Added

- `position_lifecycles`
- `exit_alternatives`
- `position_outcomes`
- `exit_quality`

All records are checksum chained through the existing Pack 3 append-only research dataset.

## Conservative Replay Rule

When a replay candle touches both a stop and a profit target and intrabar order is unknown, research assumes the stop/loss-control exit occurred first. This prevents optimistic future leakage and inflated results.

## Safety Boundary

This pack does not:

- call MT5 order check or order send
- open, modify, or close live/demo positions
- change production TP, SL, break-even, trailing, or holding logic
- change position sizing or profile policy
- promote research results into production knowledge
- select a winning policy for production use

## Validation

```powershell
.\APPLY_MILESTONE_T_PACK_4_DOC_UPDATES.ps1
.\RUN_MILESTONE_T_PACK_4.ps1
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py
python -m pytest -q
```
