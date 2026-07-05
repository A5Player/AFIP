# Production Milestone B Pack 15 — Portfolio Equity Layer

This pack introduces portfolio equity accounting as a production layer.

## Production Objective

The system can now convert account balances and profit/loss components into deterministic equity, net asset value, and portfolio-level equity summaries.

## Layer Order

1. Execution Approval
2. Order Settlement
3. Position Accounting
4. Position Valuation
5. Portfolio Equity

## Production Controls

- Negative balance review
- Negative equity review
- NAV requires ready equity
- Portfolio summary ignores unready snapshots
- Equity reconciliation enforces minimum equity and NAV/equity ratio limits

## Quality Standard

The pack uses financial terminology only and avoids non-financial naming.
