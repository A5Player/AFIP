
## Latest: Milestone S Pack 6.1
Knowledge Validation & Promotion Pipeline added. Apply as Patch Only, run focused tests and full regression. `RESEARCH_REVIEW_READY` requires human approval and does not authorize execution.


## Milestone S Pack 6.2 Handoff

Pack 6.2 adds the research-only Knowledge Certification Framework. Validated Pack 6.1 evidence can become `RESEARCH_CERTIFIED` only after sample, period, regime, stability, validation, drift, and human-review gates pass. All persistent outputs belong under `data/knowledge/certification/`. No broker, MT5, order, profile, lot-size, TP, SL, or execution policy is changed.



## Milestone S Pack 6.3 Handoff
Pack 6.3 adds research-data portability and recovery. Import defaults to verification only and applied imports use isolated bundle-ID directories. Original datasets and bundles are never silently overwritten. No trading, broker, profile, TP, SL, lot, or risk authority was added.


## Milestone S Pack 6.4 Handoff

Pack 6.4 adds knowledge/data integrity monitoring. Apply documentation updates once, run focused and full
regression tests, and keep runtime dashboard artifacts out of Git unless intentionally updated.


## Milestone S Pack 6.5 Handoff

Pack 6.5 adds the central dataset catalog. Apply documentation updates once, run focused and full
regression tests, and do not stage generated dashboard HTML unless intentionally changed.


## Milestone S Pack 6.6 Handoff

Pack 6.6 adds data quality scoring and research-readiness classification. Apply documentation updates,
run focused and full regression tests, and keep generated dashboard HTML unstaged unless intentionally changed.


## Milestone S Pack 6.7 Handoff

Run focused/full tests. No automatic deletion is permitted.


## Milestone S Pack 6.8 Handoff

Replay is offline research only and cannot execute trades.


## Milestone S Pack 6.9 Handoff

Record dataset usage before research consumption; no execution authority.


## Milestone S Pack 7.0 Handoff

All eight checks must pass. Certification remains research-only and cannot alter execution.


## Latest verified development: Milestone S Pack 7.3

Position-capacity configuration for P1-P3 is now stored as deterministic formulas and expanded into the legacy in-memory tier table at policy load time. Runtime allocation mode and Capital Growth Engine behavior remain unchanged. Legacy explicit tables remain supported. Validate with `RUN_MILESTONE_S_PACK_7_3.ps1`, full pytest, and AFIP local quality check before commit.
