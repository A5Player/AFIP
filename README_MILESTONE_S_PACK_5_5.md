# AFIP Milestone S Pack 5.5 — Position Policy Certification

This patch certifies one deterministic position-policy source shared by simulation and the demo gateway.

## Locked policy

- Confidence below 98.0: 0 units.
- 98.0–98.49: at most 1 unit.
- 98.5–99.49: at most 2 units.
- 99.5–100.0: at most 3 units.
- Confidence is a ceiling, never an instruction to force all units.
- Final allocation remains bounded by capital, profile, risk, margin, trading cost and execution capacity.
- Martingale remains prohibited.

## Profile certification

- P1 reaches 0.10 lot per unit at balance 15,000 and never grows beyond 0.10.
- P2 tier ordering and permanent 1.00 lot ceiling are regression-tested.
- P3 grows by 0.01 lot for every additional 450 balance after 0.02 and stops at 10.00 lots.
- P4 remains fixed at 0.01 for research and has no capital-tier lot growth.

## Safety

This pack does not enable live execution. Existing execution locks remain unchanged.
