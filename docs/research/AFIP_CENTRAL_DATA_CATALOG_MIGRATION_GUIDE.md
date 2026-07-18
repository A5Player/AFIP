# Migration Guide

Schema 1.0.0 is additive. Preserve stable dataset IDs across migrations.
When paths change, create a new catalog snapshot and record the old path in lineage or migration notes.
Do not rewrite historical snapshots.
