# AFIP Milestone T Pack 11

## Complete Trade Plan, Capital Stewardship and Unattended Safety Foundation

This patch introduces an execution-neutral certification authority requiring a complete plan before any later runtime layer may consider a new order.

## Permanent Rule

`NO_COMPLETE_PLAN_NO_ORDER`

A plan must contain:

1. Market Situation Plan
2. Entry Plan
3. Capital Management Plan
4. Position Care Plan
5. Exit Plan
6. Failure and Recovery Plan

Capital capacity is authoritative. Allowed units are the minimum of capital, risk, margin, exposure, correlation, and profile capacity. Confidence does not determine unit count.

The patch adds append-only datasets for complete plans, certifications, and lifecycle events. It adds stable Operations and Intelligence dashboard data contracts. It does not add an MT5 order sender, execution permission, or bypass any safety gate.
