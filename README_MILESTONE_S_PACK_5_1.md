# AFIP Milestone S Pack 5.1 — Research Data Foundation

Adds a read-only, versioned research recorder without changing trading logic or the MT5 execution path.

## Scope
- Unified research data contract `AFIP-RESEARCH-DATA-1.0`
- Append-only decision/execution events
- Atomic Trade Case Files for successfully submitted demo orders
- UTC timestamps and SHA-256 data lineage
- Pending post-trade checkpoints: M30, H1, H4, D1
- Idempotent ledger ingestion and rejected-line quarantine
- JSON/JSONL output suitable for future AFIP Gold V2 import

## Safety
The recorder never initializes MT5 and never calls order_check, order_send, position modification, or position close.
