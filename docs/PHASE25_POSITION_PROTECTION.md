# AFIP Phase 25 — Position Protection

Adds simulation-only position sizing, SL/TP planning, and profit protection planning.

Flow:
Risk-Aware Signal
→ PositionSizer
→ SLTPPlanner
→ ProtectedSimulationOrderBuilder

Safety:
- SIMULATION only
- No live execution
- All orders remain simulation objects

Next:
- Add trailing stop planner
- Add position lifecycle manager
- Add simulation journal recorder
