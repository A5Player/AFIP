# AFIP Production Batch 15.1

Institutional Runtime Integration patch.

## Install

Copy this patch into the AFIP project root so the folders merge with the existing repository.

## Validate

```powershell
python -m pytest
python tools/afip_local_quality_check.py
python afip.py simulate
git status
```

## Commit

```powershell
git add .
git commit -m "Integrate Production Batch 15 institutional intelligence runtime"
git push
```
