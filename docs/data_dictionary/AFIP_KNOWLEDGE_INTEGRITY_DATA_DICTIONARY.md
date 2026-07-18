# Data Dictionary

| Field | Meaning |
|---|---|
| report_id | Deterministic identifier derived from normalized findings |
| dataset_id | Stable dataset identifier |
| status | HEALTHY, WARNING, CORRUPTED, or QUARANTINED |
| checked_at | UTC audit timestamp |
| file_count | Number of files observed |
| findings | Ordered integrity findings |
| code | Machine-readable finding type |
| severity | WARNING or ERROR |
| path | Affected relative path or logical identifier |
| detail | Human-readable explanation |
| execution_authority | Always NONE |
| automatic_data_repair | Always PROHIBITED |
