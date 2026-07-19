# AFIP Phase U Pack 3.3.8 — Position Sizing Authority & CI Compatibility Hotfix

Patch-only overwrite package.

## Changes

- Restores backward-compatible construction of `ProfileOperationalConfig` by defaulting the two newly introduced flags.
- Enables execution participation for P1, P2 and P3 while retaining locked-simulation safety.
- Declares `CAPITAL_TIER_TABLE` as the sole sizing authority for P1-P3.
- Keeps `capital_per_unit` as legacy compatibility data only; it is not used in tier-table calculations.
- Makes legacy zero/invalid capital fail closed without division by zero.
- Updates unit allocation and capital-aware protection paths to accept authoritative tier capacity.
- Preserves P4 as `RESEARCH_FIXED_001`.

## Install

Extract this ZIP over the repository root and allow overwrite. Then run:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_3_8.ps1
```

Execution remains `LOCKED_SIMULATION_ONLY`; this pack does not enable direct/live execution.
