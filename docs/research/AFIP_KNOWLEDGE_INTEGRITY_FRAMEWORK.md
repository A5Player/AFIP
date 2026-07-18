# AFIP Knowledge Integrity Monitoring & Audit Framework

Pack 6.4 adds deterministic, research-only integrity auditing for datasets and knowledge assets.

## Status model

- HEALTHY
- WARNING
- CORRUPTED
- QUARANTINED

The framework detects missing files, checksum mismatches, invalid metadata, duplicate manifest entries,
missing guides, and broken lineage. It creates recommendations only; it never repairs or quarantines data automatically.
