# AFIP Milestone W Pack W12 — Dashboard Read Model & Freshness Validation Foundation

W12 adds a read-only consumer for the W11 advisory snapshot.

It validates:

- Required fields
- Snapshot schema version
- Digest shape
- UTC timestamp
- Future timestamp rejection
- Freshness threshold
- Certification status
- Trace completion status

Outputs:

- READ_MODEL_READY
- READ_MODEL_STALE
- READ_MODEL_BLOCKED
- READ_MODEL_WAIT

W12 does not write snapshots and has no trading, order, lot, SL/TP, or MT5 authority.
