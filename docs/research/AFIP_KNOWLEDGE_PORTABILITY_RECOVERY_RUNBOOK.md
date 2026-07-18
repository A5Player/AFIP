# Recovery Runbook

1. Preserve the source ZIP without modification.
2. Run `inspect_bundle`; quarantine the ZIP if any issue exists.
3. Run `import_bundle(..., verify_only=True)`.
4. Import to an empty isolated recovery root.
5. Compare schema versions and data dictionaries.
6. Rebuild indexes from the recovered data; never trust copied indexes blindly.
7. Record bundle ID, operator, date, reason, and destination.
8. Obtain human approval before merging recovered evidence into a current research data lake.

No recovery step may activate execution or alter P1-P4 policy.
