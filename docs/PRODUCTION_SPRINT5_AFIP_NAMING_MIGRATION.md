# Production Sprint 5 — AFIP Naming Migration

## Objective
Move the project to AFIP-first naming and remove obsolete compatibility launcher paths safely.

## Official Runtime Name
AFIP — Automated Financial Intelligence Platform

## Official Launcher
```bash
python afip.py simulate
python afip.py mt5-check
```

## Cleanup Tool
Dry-run first:
```bash
python tools/afip_naming_migration.py
```

Apply cleanup:
```bash
python tools/afip_naming_migration.py --apply
```

The cleanup tool creates a backup under `backup/` before removing obsolete compatibility paths.

## Validation
After cleanup, run:
```bash
python afip.py simulate
python afip.py mt5-check
```

## Production Lock
- Official architecture: AFIP V1 only
- Legacy architecture: closed
- Runtime status: simulation-safe
- DEMO/LIVE: still locked until the next production gate
