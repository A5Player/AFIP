# AFIP Gold V1.0 — Milestone S Pack 5.4.1

## Purpose
Restore all four demo profiles through the repository configuration source of truth.

## Root Cause
`config/four_profile_demo.json` contained `enabled=false` for P2 and P3. The configuration loader and Profile Manager correctly propagated those values, so both profiles were stopped before gateway evaluation.

## Correction
P1, P2, P3, and P4 are now configured with `enabled=true`.

No loader bypass, runtime override, safety-threshold reduction, or execution unlock is included.

## Safety State
- Execution: `LOCKED_SIMULATION_ONLY`
- Direct execution: disabled
- Live execution: disabled
- Trading-cost, spread, risk, capital, profile-policy, and permission gates: unchanged

## Validation
Run `RUN_MILESTONE_S_PACK_5_4_1.ps1` from the repository root with the virtual environment activated.
