# AFIP Runtime Flow

AFIP uses deterministic runtime evaluation. The flow is intentionally ordered so that market condition comes before trade signal interpretation.

1. Data readiness check
2. Market regime review
3. Signal context review
4. Intelligence scoring
5. Risk gate review
6. Trading cost review
7. Execution readiness review
8. Simulation decision report
9. Observability and event recording
10. Production release candidate review

No production freeze documentation step changes trading decision logic.
