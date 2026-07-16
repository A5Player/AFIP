# AFIP Gold Pro V1.0 — Milestone S Pack 5.3

## Runtime Research Data Wiring

This patch connects existing P1-P4 demo execution ledgers to the Pack 5.2 Trade Case dataset.

It adds:
- idempotent ledger ingestion,
- real holding observation recording,
- floating profit/loss, MFE and MAE,
- SL/TP context,
- closed-trade and exit-quality recording,
- profit retained and profit given back,
- M15/M30/H1/H4/D1 checkpoint wiring.

The collector is research-only. It cannot place, modify or close orders and does not affect trading decisions.
