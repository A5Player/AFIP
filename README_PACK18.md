# AFIP Production Pack 18

Runtime orchestration pack for AFIP.

## Includes

- Production quality checkpoint governance
- Runtime production orchestrator
- Executive decision report
- Production decision workflow V2
- Unit tests
- Documentation

## Install

Extract this patch into the AFIP repository root.

## Validate

```powershell
python -m pytest
python tools/afip_local_quality_check.py
python afip.py simulate
```

## Commit

```powershell
git add .
git commit -m "Add Production Pack 18 runtime orchestration"
git push
```
