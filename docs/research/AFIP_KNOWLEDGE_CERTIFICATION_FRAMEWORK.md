# AFIP Knowledge Certification Framework

## Purpose
Pack 6.2 converts validated research evidence into immutable, traceable certification records. It never changes trading policy and has no execution authority.

## Data flow
`Pack 6.1 validation evidence -> certification thresholds -> human-reviewed certification record -> lineage/version ledgers under data/knowledge/certification/`

## Certification boundary
`RESEARCH_CERTIFIED` is the highest automatic result. `PRODUCTION_CANDIDATE` is a governance label only and must not activate execution. Human review remains mandatory.

## Storage
Use JSONL for append-only ledgers and JSON for dataset metadata. Never rewrite historical rows. Corrections must be new records referencing the replaced record.

## Reuse
A future AFIP rebuild can read `dataset_info.json`, the schema guide, data dictionary, and lineage ledger without importing runtime execution modules.
