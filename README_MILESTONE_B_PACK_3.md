# AFIP Production Milestone B Pack 3

## Regime-Based Adaptive Allocation

This pack adds a production-ready regime allocation layer for Milestone B.

### Added Files
- `afip/fusion/regime_transition_matrix.py`
- `afip/fusion/volatility_weight_profile.py`
- `afip/fusion/regime_allocation_blender.py`
- `afip/fusion/regime_weight_integration.py`
- `afip/runtime/production_milestone_b_regime_runtime.py`
- `docs/PRODUCTION_MILESTONE_B_PACK_3.md`
- `tests/test_production_milestone_b_pack_3.py`

### Validate

```powershell
pytest tests/test_production_milestone_b_pack_3.py
python tools/afip_local_quality_check.py
```
