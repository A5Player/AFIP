# AFIP Production Sprint 1 — Real Simulate Command

This patch upgrades:

```powershell
python afip.py simulate
```

from a workflow display into a real SIMULATION workflow.

## Flow

Synthetic multi-timeframe candles
→ ProtectedSignalWorkflow
→ Multi-Timeframe Signal
→ Risk Gate
→ Protected Simulation Order
→ Analytics Report

## Safety

- SIMULATION only
- No MT5 live order
- No live trading
- No broker execution

## Run

```powershell
python afip.py simulate
```
