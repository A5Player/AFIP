# AFIP Configuration Center

Production Milestone H Pack 2 adds dashboard-facing configuration structure for AFIP Command Center.

## Purpose

The Configuration Center prepares account, broker, risk, dashboard, walk-forward, and capital settings for a future UI.
It does not place orders, change strategy logic, or enable live execution.

## Sections

- Broker Manager: XM Demo 100 and XM Demo 1000 account definitions.
- Risk Settings: lot size, max positions, daily loss and drawdown limits.
- Walk-Forward Settings: historical simulation, learning switch, and look-ahead protection.
- Dashboard Settings: language, refresh interval, theme, Top 10 visibility, bilingual display.
- AFIP Bank / Capital: initial capital, deposit, withdrawal, and target metadata.

## Safety Rules

- Market regime is required before signal context.
- Live execution mode is blocked in this pack.
- Login values are masked for dashboard display.
- Look-ahead protection must remain enabled.
- Runtime remains deterministic.
