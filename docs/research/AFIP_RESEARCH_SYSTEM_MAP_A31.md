# AFIP Research System Map — A31

## One-line flow

Historical closed bars → decision-time pattern candidates → blind-forward SL/TP/holding outcomes → walk-forward validation → daily participation policy → read-only ranking → later owner profile choice → existing risk and execution gates.

## Truth boundaries

- Pytest artifacts are synthetic certification evidence, not trading performance.
- A percentage always carries `%`; points always carry `points`; R values always carry `R`.
- One Setup is one trading decision. Split broker orders and 0.01-lot units are reported separately.
- Research never assigns P1–P4, promotes itself, connects to MT5, or sends an order.

## A31 policies

- SKIP_OR_TOP_1
- TOP_0_TO_3
- TOP_0_TO_5
- TOP_0_TO_10
- ONE_PER_SESSION
- ONE_PER_PATTERN_FAMILY
- DYNAMIC_DAILY_BUDGET
- SAFETY_BOUNDED_UNCAPPED (still bounded by recorded daily initial-risk R)

## Metric dictionary

- Win rate (%): winning selected Setups divided by all selected Setups × 100.
- Expectancy (R/Setup): net R divided by selected Setup count.
- Net result (R): sum of every selected Setup result after recorded costs.
- Profit factor (ratio, no unit): gross winning R divided by absolute gross losing R.
- Maximum drawdown (R): largest peak-to-trough decline of chronological cumulative R.
- No-trade days (days): calendar research days where the policy selected zero Setup.
- Marginal expectancy (R/Setup rank): expectancy of the first, second, third, etc. Setup selected within each day.

## Current dependency

A31 needs persisted A22 records containing a decision-time score and a later closed-position result. If they do not exist, the report must say WAITING_FOR_SCORED_CLOSED_OUTCOMES rather than invent performance.
