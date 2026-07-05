# AFIP Project Database

This database is the handoff record for the AFIP production repository after Production Milestone B Pack 11.

## Current Repository State

- Project: AFIP
- Completed milestone range: Production Milestone A Pack 1-12; Production Milestone B Pack 1-11
- Latest provided GitHub commit before Pack 11: `aa2dc5b`
- Pack 11 status: completed as an incremental production patch
- Test status after Pack 11: `286 passed`
- Local quality status after Pack 11: `PASS`
- Naming policy: financial terminology only

## Pack 11 Summary

Production Milestone B Pack 11 adds the Execution Approval Layer. It places a final approval step between execution planning and order submission.

Core components:

- Pre-trade compliance evaluation
- Execution approval policy
- Order submission audit record
- Production runtime integration
- Pack-specific tests
- Pack README and file list

## Required Quality Gates

Every future pack must include:

- Source files
- Runtime file
- Tests
- README
- File list
- Successful `pytest`
- Successful `python tools/afip_local_quality_check.py`

## Development Policy

- Production quality only
- Financial terminology only
- No non-financial naming conventions
- Runtime behavior must remain deterministic under simulation fallback
- Tests must cover approval, rejection, conditional review, and integrated runtime behavior
