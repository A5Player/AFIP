# Milestone W Data Contract

Every future Research Evidence envelope must include schema version, evidence ID, generated time, source lineage, dataset integrity, quarantine status, market context, matching-case count, reliability, known failure conditions and `execution_permission=false`.

Central evidence must be profile-independent. P1–P4 may filter or consume evidence but cannot own the repository. Legacy data may be read through adapters; it must not silently become authoritative. Unreliable historical periods must remain auditable and be excluded or down-weighted through explicit quarantine/integrity metadata.
