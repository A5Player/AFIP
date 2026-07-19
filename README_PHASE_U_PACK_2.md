# Phase U Pack 2 — Two Separate Dashboards

This patch replaces the single-page presentation with two independent HTML dashboards while preserving the historical DashboardUIRuntime contract.

## Dashboard 1

`runtime/dashboard/afip_profiles_dashboard.html`

- P1-P4 detailed comparison in one horizontal table.
- Each metric occupies one row and P1-P4 remain aligned in four columns.
- Account, plan, capital policy, decision, position, SL/TP, position care, profit, connection and freshness data.
- Automatic browser refresh every five seconds.

## Dashboard 2

`runtime/dashboard/afip_intelligence_research_dashboard.html`

- Every available Intelligence, Engine, Runtime, Research, Data and Certification panel.
- Categorized display.
- Top 10 visible and Top 100 expandable where ranked research records are available.
- Manual refresh button; no automatic refresh.

Trading logic, thresholds, position sizing and execution authority are unchanged.
