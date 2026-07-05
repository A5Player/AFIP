# AFIP Production Sprint 13 Patch

This patch upgrades AFIP liquidity analysis with financial-standard `LiquidityIntelligence`.

Run after applying the patch:

```bash
python tools/validate_financial_naming.py
python afip.py simulate
python afip.py mt5-check
```
