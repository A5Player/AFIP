# AFIP Phase U Pack 3.3.6
## Research Consumer Integration & Operational Profile Execution Control

This patch separates profile availability for research from permission to run execution workers.

Operational profile state after this pack:

- P1: enabled, execution enabled, research enabled
- P2: enabled, execution disabled, research enabled
- P3: enabled, execution disabled, research enabled
- P4: enabled, execution enabled, research enabled

P2 and P3 retain their configuration, runtime paths, historical data, research ledgers, and future re-enable compatibility. The demo gateway blocks them before MT5 access and before order checking or sending.

M30 remains available through the universal timeframe registry to research consumers. This patch does not automatically change any live trading policy from research results.

No lot sizing, capital gating, maximum-unit, SL, TP, risk-threshold, or order-construction rule is changed.
