# Production Milestone B Pack 20 — Production Portfolio Runtime

Pack 20 adds the production portfolio runtime layer for AFIP.

## Scope

- Integrates portfolio equity, portfolio risk, capital allocation, and portfolio analytics into one deterministic runtime state.
- Preserves existing Pack 15–19 architecture and adds only incremental source files.
- Uses financial terminology only.
- Returns review status with failed financial rules when any portfolio component is not ready.

## Source

- `afip/portfolio/production_portfolio.py`
- `afip/portfolio/__init__.py`

## Runtime

- `afip/runtime/production_milestone_b_portfolio_runtime.py`

## Tests

- `tests/test_production_milestone_b_pack_20.py`

## Validation

Required commands:

```bash
pytest
python tools/afip_local_quality_check.py
```

Expected result for this pack:

- Pytest: PASS
- AFIP Local Quality Check: PASS
- Financial Naming Validation: PASS
- AFIP Simulation: PASS
- MT5 Data Check: PASS

## Runtime Output

`ProductionMilestoneBPortfolioRuntime` exposes:

- portfolio readiness status
- equity, risk, capital, and analytics statuses
- account and position counts
- total balance, total equity, and total net asset value
- proposed risk and proposed allocation
- gross exposure, risk ratio, exposure ratio, and concentration ratio
- available capital, allocation ratio, and utilization ratio
- portfolio trend and efficiency metrics
- failed financial rules for review routing

## File List

See `AFIP_MILESTONE_B_PACK_20_FILE_LIST.txt`.
