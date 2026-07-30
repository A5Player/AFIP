# AFIP Milestone W Pack W5 — Opportunity Quality Score Runtime Foundation

W5 converts the selected plan from W4 into a deterministic advisory Opportunity Quality Score.

## Locked policy

- OQS < 97: WAIT
- 97 <= OQS < 98: ENTRY_ELIGIBLE, subject to all independent authorities
- 98 <= OQS < 99: HIGH_QUALITY
- 99 <= OQS <= 100: ELITE and eligible for Adaptive SL review

OQS never grants execution authority. Capital, Risk, Confidence and Execution remain independent authorities.

The engine fails closed when upstream status, evidence, sample size, component authority, data integrity, or any required gate is invalid.
