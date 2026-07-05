# AFIP Phase 24 — Risk-Aware Decision

Adds risk assessment before simulation order building.

Flow:
Multi-Timeframe Signal
→ RiskAssessor
→ RiskAwareDecisionService
→ SimulationOrderBuilder

Safety:
- SIMULATION only
- Live trading disabled
- High spread / low confidence / position limit can block action

Next:
- Add position sizing
- Add SL/TP planning in simulation
- Add trailing/profit protection planner
