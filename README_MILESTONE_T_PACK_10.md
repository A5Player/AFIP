# AFIP Milestone T Pack 10

## Adaptive Multi-Objective Plan Ranking, Capital Preservation Gate, Context-Aware Weighting and Profile-Specific Selection

This pack replaces single-metric ranking with a deterministic multi-objective selection policy.

Selection order:

1. Capital Preservation Gate
2. Evidence Reliability Gate
3. Current Context Match
4. Adaptive Composite Score
5. Lower drawdown and tail risk
6. Higher risk-adjusted return
7. Higher stability
8. Larger sample size
9. Higher conservative win rate
10. Higher normalized profit
11. Deterministic plan name and ID tie-breaker

Profit and win rate cannot override a failed capital or evidence gate.

Profile defaults:

- P1 prioritizes capital preservation.
- P2 uses balanced weights.
- P3 increases risk-adjusted return weight while keeping hard safety gates.
- P4 supports research comparison while retaining evidence requirements.

Context weighting is bounded and can adapt for high volatility, high-impact news, trend and range conditions. The module records Top 10, expandable Top 100 and hidden record counts for the future Intelligence dashboard.

The module does not grant execution permission and does not call MT5 order sending.
