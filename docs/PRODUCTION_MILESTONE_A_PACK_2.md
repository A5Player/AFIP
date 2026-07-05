# AFIP Production Milestone A Pack 2

This pack extends Production Milestone A with additive production-safe modules.
It keeps existing imports and runtime behavior compatible.

## A1 Adaptive Intelligence Core

Added `AdaptiveSignalCalibrator` for conservative calibration of financial
intelligence signal score and confidence values from recent outcome samples.

## A2 Market Regime Intelligence

Added `MarketRegimeTransitionIntelligence` to detect stable, unstable, and
changing market regime conditions. Changing regimes reduce exposure by design.

## A3 Learning & Optimization

Added `AdaptiveMemoryStore`, a deterministic in-memory learning record store
with export/import support for future persistence layers.

## A4 Runtime Integration

Added `ProductionMilestoneAEnhancedRuntime`, which combines calibration,
adaptive intelligence, market regime classification, regime transition checks,
and adaptive learning thresholds into one production-safe decision.

## Validation

Run:

```powershell
pytest tests/test_production_milestone_a.py tests/test_production_milestone_a_pack_2.py
python tools/afip_local_quality_check.py
```

Expected result after applying this pack on top of Milestone A:

- Milestone A pytest: 8 passed
- Milestone A Pack 2 pytest: 8 passed
- Full local quality: PASS

## Compatibility

This pack is additive only. It does not rename or remove existing public classes,
files, or runtime contracts from previous production packs.
