# AFIP Production Pack 16 - Core Decision, Portfolio, and Risk Engines

## Purpose
Production Pack 16 adds a production-ready financial engine layer for AFIP without reducing existing functionality.

## Included Engines
- DecisionEngineV2
- InstitutionalScoreEngine
- ConfluenceScoreEngine
- SignalQualityEngine
- AdaptiveRiskEngine
- PositionEngine
- PortfolioEngine
- ExposureEngine
- DrawdownEngine
- ExecutionReadinessEngine
- TradeLifecycleEngine

The word `Engine` is used in the international financial software sense: calculation engine, decision engine, risk engine, portfolio engine, and execution engine. It is not a military term.

## Integration Strategy
This pack is additive. It does not remove or overwrite existing AFIP features. It can be integrated into runtime after local quality and GitHub CI pass.

## Validation
Run:

```powershell
python -m pytest
python tools/afip_local_quality_check.py
python afip.py simulate
```

## Acceptance Criteria
- Financial naming only
- No obsolete naming
- No placeholder code
- Backward compatible
- Unit tests included
- Documentation included
- CI compatible
