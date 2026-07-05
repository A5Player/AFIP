# Production Milestone B Pack 17 — Capital Allocation Layer

Pack 17 introduces capital allocation controls for portfolio-level production readiness.

## Scope

The layer calculates reserve capital, validates allocation policy, distributes approved capital across weighted position requests, checks utilization, and publishes an integrated runtime status.

## Runtime

`ProductionMilestoneBCapitalRuntime` returns a deterministic result with reserve status, policy status, distribution status, utilization status, capital ratios, failed rules, and allocation details.

## Quality

The pack is designed to pass the AFIP financial naming standard and local quality pipeline.
