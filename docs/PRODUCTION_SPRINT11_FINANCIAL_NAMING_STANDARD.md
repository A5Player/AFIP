# Production Sprint 11 — Financial Naming Standard

AFIP now enforces international financial terminology only.

## Official naming policy

Military-style wording is obsolete and must not be used in official AFIP code, modules, logs, dashboards, or documentation.

## Approved replacements

- DecisionIntelligence → Investment Decision Controller
- TrendIntelligence → Trend Allocation Intelligence
- PrecisionEntryIntelligence → Precision Entry Intelligence
- MarketScannerIntelligence → Market Opportunity Intelligence
- EmergencyRiskHalt → Emergency Risk Halt
- MarketParticipation → Market Participation
- RiskControl → Risk Protection
- MarketSession → Trading Session
- ExecutionTool → Execution Tool

## Migration command

```bash
python tools/afip_financial_naming_migration.py
python tools/afip_financial_naming_migration.py --apply
python afip.py simulate
python afip.py mt5-check
```

The migration creates a backup before applying text changes.
