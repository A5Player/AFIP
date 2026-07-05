# AFIP Production Pack 16

Core Decision, Portfolio, Position, Adaptive Risk, Execution Readiness, and Trade Lifecycle Engines.

## Install
Extract this zip into the AFIP repository root.

Expected structure:

```text
AFIP/
  afip/engine/
  afip/report/production_readiness_report.py
  tests/test_production_pack16_*.py
  docs/PRODUCTION_PACK16_CORE_DECISION_PORTFOLIO_RISK.md
```

## Validate

```powershell
python -m pytest
python tools/afip_local_quality_check.py
python afip.py simulate
```

## Commit

```powershell
git add .
git commit -m "Add Production Pack 16 core decision portfolio risk engines"
git push
```
