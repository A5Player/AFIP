
## Phase U Pack 3.3.1 — Universal Timeframe Registry
Status: PATCH DELIVERED; USER-SIDE VALIDATION REQUIRED

Architecture:
- `afip/timeframe_registry.py` is the canonical deterministic timeframe source.
- Supported order: M1, M5, M15, M30, H1, H4, D1.
- Capabilities are recorded per timeframe for historical collection, replay, research, gap detection and dashboard use.
- Automatic research MT5 mapping resolves constants from registry metadata.

Safety:
- Live execution authority unchanged.
- No order send path added.
- No risk threshold, capital gate, maximum unit, SL or TP policy changed.
- Append-only research history preserved.
