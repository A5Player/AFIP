# AFIP Milestone S Pack 4.2 — Demo Execution Trading Cost Contract Recovery

## Verified root cause

`TradingCostIntelligence` defines `CAUTION` as executable when `allowed=True`, but the demo gateway previously accepted only `status == PASS`. This blocked valid caution-band spreads before `order_check` and `order_send`.

## Production correction

- The gateway now uses the authoritative `allowed` contract.
- `PASS` and `CAUTION` may proceed only when `allowed=True`.
- `BLOCK` remains blocked.
- Unknown or missing cost statuses fail closed.
- No spread threshold, confidence threshold, position sizing rule, or safety arm was weakened.
- Gateway reports now record spread thresholds, point size, digits, and MT5 call/result visibility.

## Validation result in source repository

- Pack regression: `13 passed`
- Pack + dashboard regression: `15 passed`
- Full test suite: `1808 passed`
