# AFIP Phase U Pack 3.4.5

## Research Dashboard

This patch extends the research architecture without changing live order transmission,
position sizing, stop-loss placement, profit targets, or profile account mapping.

Drawdown is a mandatory, non-compensating research condition. A high win rate cannot
override a drawdown breach.

## Validation

Run:

```powershell
.\APPLY_PHASE_U_PACK_3_4_5_DOC_UPDATES.ps1
.\RUN_PHASE_U_PACK_3_4_5.ps1
```
