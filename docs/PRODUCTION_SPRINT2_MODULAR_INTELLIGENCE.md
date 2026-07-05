# AFIP Production Sprint 2 — Modular Intelligence Pack

This patch starts the 80–120 Intelligence roadmap by adding a clean modular Intelligence framework with 14 production-oriented modules.

## Added Intelligence

- Market Intelligence V2
- Trend Strength Intelligence
- Momentum Quality Intelligence
- Liquidity Quality Intelligence
- Volume Intelligence
- Order Flow Intelligence
- Volatility Risk Intelligence
- Correlation Intelligence
- News Risk Intelligence
- Risk Intelligence
- Portfolio Intelligence
- Execution Intelligence
- Performance Intelligence
- Learning Intelligence

## Flow

Market Snapshot
→ Modular Intelligence Pipeline
→ Decision Intelligence
→ Transparent Explanation

## Run

```powershell
python afip.py simulate
```

## Safety

- SIMULATION only
- No live order
- No broker execution

## Next Sprint

Production Sprint 3:
- Real MT5 tick/candle reader
- CLI: `python afip.py mt5-check`
- CLI: `python afip.py simulate --source mt5`
- DEMO-only preparation, no live order
