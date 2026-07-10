# Production Bring-up Pack 9 — Runtime Supervisor

Adds a deterministic, read-only supervisor for AFIP runtime dependencies. It aggregates dashboard, MT5, internet, calendar, historical-data, live-dashboard, and intelligence health into one explainable report.

The supervisor never submits orders, never enables live execution, and does not modify trading logic. Version 1 remains restricted to XM and GOLD#.

Dashboard output includes runtime health, healthy/warning/critical module counts, bilingual recovery guidance, supervisor confidence, and the expected next review.
