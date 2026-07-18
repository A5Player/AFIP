# Data Dictionary

| Field | Meaning |
|---|---|
| dataset_id | Stable identity independent from profile or preset |
| name | Human-readable dataset name |
| category | Dataset family such as MARKET_DATA or DATA_GOVERNANCE |
| schema_version | Dataset schema version |
| storage_path | Canonical path under `data/` |
| owner | Accountable owner |
| producer | Module or process that creates the data |
| classification | Data usage classification |
| lifecycle_status | ACTIVE, DEPRECATED, ARCHIVED, or QUARANTINED |
| retention_policy | Retention rule |
| lineage_parents | Parent dataset IDs |
| guides | Documentation paths |
| tags | Search and classification tags |
| execution_authority | Always NONE |
