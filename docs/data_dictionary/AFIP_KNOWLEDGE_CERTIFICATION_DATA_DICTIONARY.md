# AFIP Knowledge Certification Data Dictionary

| Field | Meaning |
|---|---|
| certification_id | Deterministic identifier for one certification decision. |
| knowledge_id | Stable identity of the knowledge concept. |
| knowledge_version | Immutable version label of the evaluated knowledge. |
| parent_certification_id | Previous certification in the lineage, when present. |
| certification_level | Governance level; never execution permission. |
| decision | `CERTIFICATION_PENDING`, `REJECTED`, or `RESEARCH_CERTIFIED`. |
| lifecycle_state | Current research lifecycle state. |
| evidence_ids | Deduplicated source evidence identifiers. |
| independent_periods | Distinct blind/forward research periods. |
| market_regimes | Distinct regimes represented by evidence. |
| sample_size | Total evaluated observations. |
| average_validation_score | Mean Pack 6.1 validation score. |
| average_stability_score | Mean evidence stability score. |
| maximum_drift_score | Worst observed drift score. |
| reviewer | Human or governance reviewer identity. |
| evaluated_at | UTC certification evaluation timestamp. |
| reasons | Machine-readable decision reasons. |
| execution_authority | Always `NONE`. |
