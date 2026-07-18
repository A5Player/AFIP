# Technical Guide

Use `KnowledgeIntegrityAuditor.audit_dataset()` with a dataset directory, optional manifest,
required guide paths, and optional lineage records. Reports are deterministic except for `checked_at`.
`report_id` is derived from dataset ID, file count, and normalized findings.
