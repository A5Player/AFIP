
## Milestone S Pack 7.1 — Position Ceiling Semantics Correction

- Position policy upgraded to AFIP_POSITION_POLICY_V2.
- Confidence defines maximum Unit capacity only.
- Balance tiers define maximum lot per Unit and available slots only.
- Intelligence explicitly requests the actual Unit count; absent request defaults to one eligible Unit.
- Automatic fill-to-ceiling is prohibited.
- P1 0.10 threshold corrected to 16,500; P2 0.10 threshold corrected to 15,000.
- P1/P2/P3 permanent per-Unit ceilings remain 0.10/1.00/10.00 respectively.
- P4 remains fixed 0.01 research allocation without lot growth.
- Full regression: 2076 passed.
