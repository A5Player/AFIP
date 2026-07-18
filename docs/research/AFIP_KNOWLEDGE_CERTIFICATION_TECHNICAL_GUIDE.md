# Technical Guide — Knowledge Certification

The runtime is deterministic when `evaluated_at` is supplied. IDs are SHA-256-derived from canonical JSON. Evidence is deduplicated by `evidence_id`. Policy validation enforces no execution authority, prohibited execution promotion, prohibited automatic strategy changes, and mandatory human review.

Persistent data belongs under `data/knowledge/certification/`. Source modules must not store credentials, broker handles, tickets, lots, or order requests.
