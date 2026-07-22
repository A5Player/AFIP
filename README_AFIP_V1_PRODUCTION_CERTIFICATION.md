# AFIP V1 Production Certification

This pack closes the validation layer after Final Consolidation.

## Authorities

- Final Consolidation remains the runtime architecture authority.
- Production Certification is validation-only.
- Research code receives no execution authority.
- Existing repository and runtime data are preserved.

## Main improvement

The legacy financial naming validator is preserved as
`tools/validate_financial_naming_legacy.py`.

The public command `tools/validate_financial_naming.py` becomes a backward-
compatible incremental wrapper. It creates a temporary filtered source mirror,
excluding runtime data, generated dashboards, backups, caches and virtual
environments. A successful repository fingerprint is cached.

## Commands

Targeted certification:

```powershell
.\RUN_AFIP_V1_PRODUCTION_CERTIFICATION.ps1
```

Full certification:

```powershell
.\RUN_AFIP_V1_PRODUCTION_CERTIFICATION.ps1 -FullRegression
```

Operational MT5 check may be included:

```powershell
.\RUN_AFIP_V1_PRODUCTION_CERTIFICATION.ps1 -FullRegression -Mt5Check
```

A production-ready certificate requires full regression PASS.
