# AFIP Blind Forward Research Guide

## Boundary

The Blind Forward Research Engine is a research sidecar. It receives a frozen research case, an externally versioned candidate set, and chronological closed bars. It cannot route, size, check, or send an order.

## Forward-only contract

Every evaluated bar must close strictly after `entry_at_utc`. Bars must be strictly chronological. Any future-data flag in provenance invalidates the case before evaluation.

## Candidate evaluation

Each TP/SL combination is evaluated with the unrestricted end-of-data path and with each configured time exit. Candidate values are points converted by the research case `point_size`.

## Conservative ambiguity rule

OHLC bars do not reveal intrabar ordering. When both TP and SL are reachable inside one bar, the result is recorded as `STOP_LOSS` with `same_bar_collision=true`.

## Metrics

Each outcome records result points, exit reason, exit time, holding bars, holding seconds, maximum favorable excursion and maximum adverse excursion.

## Determinism and storage

Canonical JSON of case, candidate set and evaluated bars produces the input SHA-256. Stable evaluation fields produce the result ID. `evaluated_at_utc` is audit metadata and is excluded from deterministic identity. Results are appended to date-partitioned JSONL. Duplicate IDs are skipped.

## Eligibility

A case is quarantined when forward bars are missing, data quality is not PASS, market regime is missing, pattern family is missing, or features are missing. Quarantined cases create no candidate outcomes.

## Execution isolation

`execution_authority` is always `NONE`. Promotion to execution is prohibited. Research results may be consumed by later certified knowledge processes only after separate governance and production-readiness approval.
