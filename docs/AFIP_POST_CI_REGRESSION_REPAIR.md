# AFIP Post-CI Regression Repair

This patch resolves the three full-regression failures observed after the
Python 3.11 audit-tool compatibility repair.

## Runtime correction

After demo MT5 preflight verifies the exact account/server/terminal binding,
all downstream WAITING or BLOCKED reports retain:

- masked connected login
- connected/configured terminal folders
- ownership token
- binding verification
- balance/equity
- available capital
- capital basis

No execution gate is weakened and no order path is added.

## Research contract alignment

The dashboard regression fixtures now use the current research evidence
contract:

- `research_feedback_status = ELIGIBLE`
- `net_realized_profit_usd`

The aggregator remains unchanged. Ineligible or legacy-incomplete feedback is
not promoted into production research statistics.
