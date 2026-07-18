# Data Dictionary — Knowledge Portability

| Field | Meaning |
|---|---|
| schema_version | Manifest contract version |
| bundle_id | Deterministic identity derived from dataset name, metadata, and entries |
| dataset_name | Human-readable dataset identity |
| source_root | Audit-only source path at export time |
| created_at_utc | Manifest creation time |
| file_count | Number of payload files |
| total_size_bytes | Sum of payload sizes |
| relative_path | Portable POSIX-style path within payload |
| size_bytes | Exact raw byte count |
| sha256 | SHA-256 checksum of raw bytes |
| category | First path segment or `root` |
| metadata | Research-defined provenance and schema context |
| execution_authority | Always `NONE` |
| promotion_to_execution | Always `PROHIBITED` |
