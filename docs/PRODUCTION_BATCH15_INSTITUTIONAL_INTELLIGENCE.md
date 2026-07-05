# AFIP Production Batch 15 — Institutional Intelligence

Production Batch 15 adds read-only institutional market structure analysis to AFIP using international financial terminology only.

## Components

1. `FairValueGapIntelligence`
   - Detects bullish and bearish three-candle fair value gaps.
   - Reports gap bounds, gap size, fill percentage, state, quality, and directional score.

2. `ImbalanceIntelligence`
   - Measures directional candle pressure, expansion strength, body quality, and market efficiency.
   - Reports imbalance score, efficiency score, expansion strength, and directional bias.

3. `OrderBlockIntelligence`
   - Detects bullish and bearish order block zones created before displacement.
   - Reports fresh, mitigated, or broken state with zone strength.

4. `LiquiditySweepIntelligence`
   - Detects buy-side and sell-side liquidity sweeps with rejection confirmation.
   - Reports reference levels, sweep extremes, confirmation close, and confidence.

5. `SmartMoneyConceptIntelligence`
   - Integrates the four institutional components into one institutional bias.
   - Outputs `BUY`, `SELL`, or `FLAT` with confidence and component details.

## Input Contract

Each component accepts a `snapshot` dictionary with OHLC arrays:

```python
{
    "opens": [100.0, 100.5, ...],
    "highs": [101.0, 101.5, ...],
    "lows": [99.5, 100.1, ...],
    "closes": [100.8, 101.2, ...],
    "spread": 25.0,
}
```

`spread` is optional for Batch 15 modules.

## Output Contract

Every component returns a dictionary with at least:

```python
{
    "name": "ComponentName",
    "status": "READY",
    "direction": "BUY",
    "confidence": 76.5,
    "reason": "component_reason",
    "buy_score": 76.5,
    "sell_score": 0.0,
}
```

## Production Safety

- Read-only analysis only.
- No order execution.
- No change to existing AFIP runtime behavior unless explicitly wired later.
- Backward compatible with existing snapshot-style intelligence modules.
- Uses financial market terminology only.

## Validation

Run from repository root:

```bash
python -m pytest tests/test_production_batch15_institutional_intelligence.py
python tools/afip_local_quality_check.py
```
