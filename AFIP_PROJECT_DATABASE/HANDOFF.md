# AFIP Handoff — Production Bring-up Pack 6

## Authoritative Base

- User repository archive plus incremental Pack 4 and Pack 5 patches
- Latest verified GitHub commit before queued patches: `826552a`
- Pack 4 verified: 6 targeted tests, 970 full tests, quality PASS, dashboard PASS, Git push completed
- Pack 5 is queued for user validation before Pack 6 installation

## Pack 6 — AFIP Bank Live

Adds a deterministic read-only capital ledger with bilingual dashboard explanation.

### Added

- `AFIPBankLiveRuntime`
- Deposit and withdrawal ledger
- Closed and floating trading profit separation
- Balance, equity, reserve and available allocation
- Lifetime return calculation
- Transaction audit records
- XM-only and GOLD#-only policy gates
- Explicit live-execution block
- English and Thai documentation
- Pack tests and RUN scripts

### Safety

- Live execution remains disabled.
- No money transfer capability is introduced.
- No broker order capability is introduced.
- Trading logic changed: false.
- Unsupported broker, symbol, live mode and excessive withdrawal states are explicitly blocked.

## Installation Order

1. Validate and push Pack 5.
2. Extract Pack 6 into the same repository root.
3. Run `RUN_PRODUCTION_BRINGUP_PACK_6.ps1` or the provided commands.
4. Do not skip packs or install them out of order.

## Next Step

After Pack 6 passes on the user's VPS, continue to Production Bring-up Pack 7 — Historical Data Manager.

# AFIP Handoff — Production Bring-up Pack 7

Adds a bilingual, read-only Historical Data Manager dashboard panel. It preserves the existing Milestone H historical modules and adds production visibility for timeframe coverage, data quality, research readiness, walk-forward readiness and next action. XM and GOLD# remain the only Version 1 policy. Live execution remains disabled. Install after Pack 6. Next: Production Bring-up Pack 8 — Dashboard Live Runtime.
