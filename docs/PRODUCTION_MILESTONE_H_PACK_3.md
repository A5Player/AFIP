# Production Milestone H Pack 3 — Profile Manager, Setup Wizard, Connection Manager, Historical Data Manager, Dashboard Runtime

## Scope

Pack 3 adds dashboard-facing managers for Version 1 VPS preparation:

- Profile Manager
- Setup Wizard
- Connection Manager
- Historical Data Manager
- Dashboard Runtime Status Composer

## Production Policy

- Broker: XM only
- Symbol: GOLD# only
- Multi broker: disabled for Version 1
- Live trading: disabled in this pack
- Execution modes allowed: SIMULATION, PAPER, PAPER_TRADING, LOCKED_SIMULATION_ONLY

## Profile Architecture

A Profile is a reusable trading policy.

A Profile is not an Account.
A Profile is not MT5.
A Profile is not Demo or Real.

One Profile can be assigned to any account, and one account can switch Profiles.

## Unit System

1 Unit = 0.01 lot.

AFIP does not increase lot size directly. AFIP increases approved Unit count.

Example:

- 1 Unit = 0.01
- 3 Units = 0.01 + 0.01 + 0.01

## Setup Wizard

The wizard tracks:

1. Welcome
2. Broker
3. Login
4. MT5 Path
5. Download Historical Data
6. Profile Selection
7. Test Connection
8. Save
9. Run AFIP

Run AFIP becomes available only after required setup steps are ready.

## Connection Manager

The dashboard runtime can display:

- Internet status
- Internet disconnect count
- Internet disconnect duration
- Reconnect count
- MT5 status
- Broker status
- CPU
- RAM
- Disk
- Runtime
- Market open or close
- Trading session
- Profile
- Waiting reason

## Historical Data Manager

Pack 3 validates historical data readiness for:

- Automatic download workflow preparation
- Missing bars
- Duplicate bars
- Quality score
- Walk Forward readiness
- Research readiness

## Dashboard Runtime

Dashboard Runtime composes status from Profile Manager, Setup Wizard, Connection Manager, and Historical Data Manager.

Dashboard sections include:

- Runtime
- Intelligence
- Engine
- Trading
- Analytics
- AFIP Bank
- Research
- System
- Market

Order Center sections include:

- Waiting
- Reason
- Ready
- Opened
- Managing
- Closing
- Closed
- Close Reason
- Order Quality

Decision explainability sections include:

- Waiting
- Entry
- Holding
- Trailing Stop
- Break Even
- Stop Loss Move
- Partial Close
- Final Close
- Rejected Entry
- Rejected Exit
- Alternative Decision
- Current AI Reasoning

## Safety

This pack changes dashboard and setup readiness only.
It does not change trading logic.
It does not enable live trading.
