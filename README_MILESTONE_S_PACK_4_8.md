# Milestone S Pack 4.8 — Capital Growth Engine and Operator Visibility

This patch separates capital-tier calculation from the MT5 demo gateway while preserving the existing gateway contract.

It adds live diagnostics for current tier, target lot distribution, next tier, remaining balance to the next tier, maximum tier, and withdrawal reference. Amounts above the final tier do not increase lot size. No automatic withdrawal is performed.
