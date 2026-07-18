# Milestone S Pack 7.1 — Position Ceiling Semantics Correction

This patch makes Confidence and Balance values strict maximum ceilings rather than automatic full-allocation targets.

Key changes:

- Missing Intelligence Unit request defaults conservatively to 1 Unit.
- Explicit requests may use 1, 2 or 3 Units but are reduced by the Confidence ceiling.
- P1 0.10 tier starts at balance 16,500 and remains permanently capped at 0.10 per Unit.
- P2 0.10 tier starts at balance 15,000 and continues to the existing 1.00 ceiling.
- P3 retains the approved 450-balance growth progression through the 10.00 ceiling.
- P4 remains fixed at 0.01 per Unit with no lot growth and no total research Unit ceiling.
- Gateway diagnostics now record requested Units, Confidence ceiling and Unit-selection reason.

Focused validation: 28 passed.
Full regression on the supplied repository: 2076 passed.
