# Recovery Runbook

1. Stop writers to the affected dataset.
2. Preserve the current directory as evidence.
3. Verify the latest trusted manifest and portable bundle.
4. Compare missing and changed files.
5. Restore into a separate recovery directory.
6. Re-run integrity audit.
7. Approve replacement manually.
8. Record the incident and resolution in append-only ledgers.
