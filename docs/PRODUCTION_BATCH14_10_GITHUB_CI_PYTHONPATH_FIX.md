# Production Batch 14.10 — GitHub CI Python Path Fix

## Purpose
Fix GitHub Actions test discovery when the `afip` package is not found on the Linux runner.

## Root Cause
Local Windows runs execute from the project directory where Python can resolve the local `afip` package. GitHub Actions runs inside the checkout workspace, but the workflow did not explicitly export the project root into `PYTHONPATH` for pytest collection.

## Fix
Updated `.github/workflows/ci.yml` to set:

```yaml
env:
  PYTHONPATH: ${{ github.workspace }}
```

## Validation
Run locally before commit:

```bash
python tools/afip_local_quality_check.py
```

Then commit and push:

```bash
git add .
git commit -m "Production Batch 14.10: Fix GitHub CI Python path"
git push
```

After push, check GitHub Actions again.
