# AFIP Phase 20 — MT5 Adapter Interface

This patch adds a safe MT5 adapter interface.

## What changed

- `MT5Adapter`
- `MT5MarketDataProvider`
- `MarketDataContract`
- Updated `MarketSignalWorkflow`

## Safety

- No live order execution
- No direct order sending
- MT5 disabled by default
- Falls back to simulation when unavailable

## Next

Phase 21 should add candle normalization:
- OHLCV model
- timeframe adapter
- spread normalization
- session metadata
- integration test using synthetic candle batches
