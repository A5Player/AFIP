# AFIP Phase U Pack 3.3.10

## Production Contract Alignment

This patch aligns historical-data validation and profile execution regression contracts with the current production policy.

### Production contract

- P1: execution enabled
- P2: execution enabled
- P3: execution enabled
- P4: research only; execution disabled
- Historical readiness requires the universal timeframe set: M1, M5, M15, M30, H1, H4, D1

### Safety scope

- Patch only
- No trading signal logic change
- No position-sizing logic change
- No order-management logic change
- Direct/live execution locks remain unchanged
- Research participation remains enabled for P1-P4

### Verified result

- Targeted regression: 20 passed
- Full regression: 2409 passed
- AFIP Local Quality Check: PASS
- Dashboard generation: PASS
