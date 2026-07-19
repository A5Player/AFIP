# AFIP Phase U Pack 3.3.4
## M30 Research Data Quality, Gap Detection & Automatic Backfill

This patch extends the universal timeframe research foundation with deterministic data-quality evidence for M1, M5, M15, M30, H1, H4, and D1.

Implemented:
- Registered-timeframe integrity validation.
- Exact timestamp duplicate detection.
- Deterministic missing-bar and gap-range evidence.
- Timeframe-specific freshness evidence.
- Provider-driven automatic backfill merging.
- MT5 historical gap backfill support for research collection only.
- Append-only persistence of accepted historical backfill bars.
- Automatic research status fields for quality, gaps, freshness, and backfill.
- Full M30 participation in research quality and backfill paths.

Safety:
- No order execution authority was added.
- Live trading policy, lot sizing, capital gating, maximum units, SL, and TP were not changed.
- Existing historical and research records are never rewritten.
- Existing records win during deterministic merge; duplicates are skipped.
