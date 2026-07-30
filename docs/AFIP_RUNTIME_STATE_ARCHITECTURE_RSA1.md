# AFIP Runtime State Architecture — RSA-1

## Purpose

RSA-1 classifies modified, deleted, and untracked repository files without changing repository or runtime state.

## Categories

- `RUNTIME_STATE`
- `RESEARCH_DATA`
- `DASHBOARD_CACHE`
- `PRODUCTION_EVIDENCE`
- `CERTIFICATION_EVIDENCE`
- `TEMPORARY_PROCESS_STATE`
- `PERSISTENT_KNOWLEDGE`
- `UNCLASSIFIED`

## Safety contract

RSA-1 never moves, deletes, restores, untracks, or ignores files. It only writes reports under:

`runtime/control/runtime_state_architecture/rsa1/`

The report becomes the input contract for RSA-2 Runtime Persistence Policy.
