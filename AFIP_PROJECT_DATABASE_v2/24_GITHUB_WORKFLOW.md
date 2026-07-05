# AFIP GitHub Workflow

## Source of Truth

GitHub repository is the official source of truth for AFIP.

Repository:

```text
https://github.com/A5Player/AFIP
```

## Required Local Validation

Before every push, run:

```bash
python tools/afip_local_quality_check.py
```

## Required GitHub Validation

GitHub Actions must pass after every push.

Workflow file:

```text
.github/workflows/ci.yml
```

## Naming Rule

AFIP must use international financial terminology only.

Military terminology is prohibited.

## Next Production Batch

Production Batch 15 should continue with Fair Value Gap Intelligence and Order Block Intelligence under the Financial Naming Standard.
