# AFIP Production Pack 17

Analytics, backtest metrics, scenario validation, and runtime reporting.

## Install

Extract this archive into the AFIP repository root.

## Validate

```powershell
python -m pytest
python tools/afip_local_quality_check.py
python afip.py simulate
```

## Commit

```powershell
git add .
git commit -m "Add Production Pack 17 analytics backtest reporting"
git push
```
