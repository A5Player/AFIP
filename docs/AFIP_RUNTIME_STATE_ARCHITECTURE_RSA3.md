# AFIP Runtime State Architecture — RSA-3

## Purpose

Combine RSA-2 persistence policy and RSA-2.1 manual-review resolutions into a
single safe Git tracking and runtime separation plan.

## Scope

RSA-3 is plan-only. It does not mutate Git, `.gitignore`, runtime files,
archives, or external data locations.

## Output

- Every changed/untracked file receives an explicit planned action.
- Actions are grouped by source, generated runtime, research persistence,
  production archive, certification snapshot, and temporary process state.
- A strict execution order is produced for the guarded implementation phase.
