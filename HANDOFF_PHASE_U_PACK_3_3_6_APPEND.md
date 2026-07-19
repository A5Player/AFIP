
## Phase U Pack 3.3.6 Handoff — Profile Execution / Research Separation

Verified intended operational state:

- P1 execution enabled, research enabled
- P2 execution disabled, research enabled
- P3 execution disabled, research enabled
- P4 execution enabled, research enabled

`enabled` remains true for P2/P3, preserving configuration and research participation. Re-enabling later requires only changing `execution_enabled` to true; no data migration is required.

Safety boundary: this pack does not certify real-account readiness and does not verify or change lot sizing, capital gating, maximum units, SL, TP, or execution protection parameters.
