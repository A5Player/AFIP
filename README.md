# AFIP Production Batch 14.9 — Final Data Source Compatibility Fix

Run from the AFIP project root:

```bash
python tools/afip_batch14_9_final_data_source_compatibility_fix.py
python tools/afip_local_quality_check.py
```

If the local quality gate passes:

```bash
git add .
git commit -m "Production Batch 14.9: Finalize data source compatibility"
git push
```
