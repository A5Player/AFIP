# Validation Guide

Run:

```powershell
.\VALIDATE_PHASE_U_PACK_3_4_9.ps1
```

Required checks:

- Pack tests pass.
- Full regression passes.
- Local quality check passes.
- Financial output contains no invented 1000 values.
- Portfolio totals remain unavailable unless all four profiles are verified.
- Cross-market sources report actual MT5 symbols or `DATA_UNAVAILABLE`.
- All cross-market relationships remain `RESEARCH_ONLY`.
- Dashboard does not mark missing sources READY.
