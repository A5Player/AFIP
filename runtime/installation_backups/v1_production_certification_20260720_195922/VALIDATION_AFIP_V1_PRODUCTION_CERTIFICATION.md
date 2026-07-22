# Validation Contract

The certification runner records every check independently.

Required for targeted PASS:
- Final Consolidation tests
- Compatibility certification tests present in repository
- Architecture command
- Dashboard build
- Incremental financial naming validation
- Local quality check when present

Required for `production_ready=true`:
- All targeted checks PASS
- Full repository regression requested and PASS

MT5 check is operational certification and is included only when explicitly
requested with `-Mt5Check`.
