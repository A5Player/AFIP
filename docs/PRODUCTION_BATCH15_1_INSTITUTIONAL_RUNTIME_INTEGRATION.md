# Production Batch 15.1 - Institutional Runtime Integration

Batch 15.1 connects the institutional intelligence modules introduced in Batch 15 into the default AFIP modular intelligence catalog and runtime simulation display.

## Scope

- Add Fair Value Gap Intelligence to the default intelligence catalog.
- Add Imbalance Intelligence to the default intelligence catalog.
- Add Order Block Intelligence to the default intelligence catalog.
- Add Liquidity Sweep Intelligence to the default intelligence catalog.
- Add Smart Money Concept Intelligence to the default intelligence catalog.
- Display Institutional Intelligence inside the simulation CLI output.
- Preserve the existing RuntimeV1 return schema and backward compatibility.

## Files

- `afip/registry/intelligence_catalog.py`
- `afip/cli/simulate.py`
- `tests/test_production_batch15_1_institutional_runtime_integration.py`
- `docs/PRODUCTION_BATCH15_1_INSTITUTIONAL_RUNTIME_INTEGRATION.md`
- `README_BATCH15_1.md`

## Validation

Run from the AFIP project root:

```powershell
python -m pytest
python tools/afip_local_quality_check.py
python afip.py simulate
```

Expected result:

- Pytest passes.
- Local quality passes.
- Simulation output includes `Institutional Intelligence`.
- No obsolete naming is introduced.

## Backward Compatibility

The existing RuntimeV1 simulation structure is preserved. The integration is additive: existing intelligence modules remain in the catalog and institutional modules are appended after the existing default modules.
