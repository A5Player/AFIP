
## AFIP V1 Production Finalization Big Pack

- Unified P1-P4 execution architecture; P4 is Experimental execution profile.
- Research remains independent in Research Runtime and Data Lake.
- Added AFIP V1 Production Runtime Authority for canonical dashboard snapshot and safe stale-control cleanup.
- Sequential Router remains process-isolated and now performs safe startup cleanup.
- MT5 routing lock recovery is PID-aware and does not steal a lock from a living owner.
- Dashboard enrichment now uses one production authority snapshot.
- Updated obsolete regression contracts that encoded P4 as research-only.
- Pack build validation: 76 passed.
