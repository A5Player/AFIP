# AFIP Production Batch 15

Adds institutional intelligence modules:

- Fair Value Gap Intelligence
- Imbalance Intelligence
- Order Block Intelligence
- Liquidity Sweep Intelligence
- Smart Money Concept Integration

Copy the `afip/`, `tests/`, and `docs/` folders into the AFIP repository root, then run:

```bash
python -m pytest tests/test_production_batch15_institutional_intelligence.py
python tools/afip_local_quality_check.py
python afip.py simulate
```

Commit command:

```bash
git add .
git commit -m "Production Batch 15: Add institutional intelligence"
git push
```
