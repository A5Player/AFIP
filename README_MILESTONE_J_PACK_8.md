# Milestone J Pack 8 — Exit Validation Engine

Adds deterministic, explainable validation for holding, stop-loss moves, take-profit changes, trailing stops, partial closes, and full exits.

Policy:
- XM only
- GOLD# only
- Paper/demo context only
- No direct execution
- Live execution remains disabled
- 1 Unit remains 0.01 lot

The engine never modifies or closes a position. It produces an approved management context for later paper/demo review.
