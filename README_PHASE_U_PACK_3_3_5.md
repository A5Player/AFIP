# AFIP Phase U Pack 3.3.5

## Dashboard Coverage, Progress, Freshness & Research Status Integration

This patch adds a structured, deterministic universal-timeframe status table to Dashboard 3.

Displayed for M1, M5, M15, M30, H1, H4 and D1:

- available and valid bars
- detected gaps and missing bars
- freshness state
- replay bars processed in the current run
- covered bars and replay completion
- integrity status
- research eligibility

The Automatic Research Runtime panel now displays selected scalar evidence instead of dumping nested dictionaries. Backward-compatible three-dashboard output and the legacy Dashboard 2 redirect are preserved.

Research evidence remains presentation-only and cannot change live trading policy or send orders.
