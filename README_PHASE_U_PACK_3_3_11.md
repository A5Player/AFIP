# AFIP Phase U Pack 3.3.11

## Runtime Research Data Git Isolation

This pack separates reproducible runtime research data from the AFIP source repository without deleting local or VPS datasets.

### Scope

- Ignore generated automatic-research JSONL streams.
- Ignore the historical data lake and resumable research working areas.
- Remove five already tracked schema-v2 streams from the Git index only.
- Preserve all files on disk.
- Keep source code, configuration, tests, documentation, and committed fixtures under Git control.
- Do not change trading logic, risk policy, profile sizing, execution permissions, or live-account arming.

### Install and apply

Extract this ZIP over the existing repository, then run:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\APPLY_PHASE_U_PACK_3_3_11.ps1
.\RUN_PHASE_U_PACK_3_3_11.ps1
git status
```

The deleted entries shown by `git status` are index removals. The runtime files remain present locally and become ignored after commit.
