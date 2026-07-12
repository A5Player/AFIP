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

## Version 1.0 Milestone S Pack 2
Four-profile demo operations are available through `config/four_profile_demo.json` and `tools/afip_four_profile_control.py`. See `README_MILESTONE_S_PACK_2.md` and `README_MILESTONE_S_PACK_2_TH.md`. Live execution remains disabled.
