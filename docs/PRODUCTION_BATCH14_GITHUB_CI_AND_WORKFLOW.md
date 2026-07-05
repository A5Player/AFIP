# Production Batch 14 — GitHub CI and Workflow

## Status

Ready for local installation.

## Objective

Stabilize AFIP development by adding GitHub Actions and a local quality check script.

## Added Files

- `.github/workflows/ci.yml`
- `tools/afip_local_quality_check.py`
- `docs/GITHUB_WORKFLOW_GUIDE.md`
- `docs/PRODUCTION_BATCH14_GITHUB_CI_AND_WORKFLOW.md`
- `AFIP_PROJECT_DATABASE_v2/24_GITHUB_WORKFLOW.md`

## Validation Commands

```bash
python tools/afip_local_quality_check.py
```

or manually:

```bash
python tools/validate_financial_naming.py
python afip.py simulate
python afip.py mt5-check
pytest -q
```

## Expected Result

- Financial naming validation passes.
- AFIP simulation passes.
- MT5 check passes locally on the user's machine.
- Tests pass.
- GitHub Actions runs after push.
