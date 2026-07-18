# AFIP Milestone S Pack 5.6 — Research Data Foundation

This patch establishes AFIP's versioned, machine-readable research-data contracts without changing execution mode or order behavior.

## Scope

- Central profile-independent Data Dictionary.
- Score Dictionary with components, formula references, and separate hard gates.
- Formula Registry and recomputation metadata.
- Data-quality dimensions and statuses.
- Research-eligibility and quarantine rules.
- Decision Trace envelope API.
- Human-readable research guides.
- Regression validation.

## Safety

This pack does not unlock Demo or Live execution, does not change thresholds, does not send orders, and keeps raw research data immutable.

## Validation

```powershell
.\RUN_MILESTONE_S_PACK_5_6.ps1
python tools\afip_local_quality_check.py
```
