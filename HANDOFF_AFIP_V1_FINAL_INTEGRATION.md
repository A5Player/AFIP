# HANDOFF — AFIP V1 Final Integration

Source repository inspected: uploaded AFIP(44).zip, repository root `AFIP/source`.
Observed commit: `8bd57f9 Complete Phase U financial integrity and research runtime integration`.
Observed working tree: heavily modified and uncommitted; this pack must be applied without reset, checkout, clean, or destructive migration.

Final authority:
- `python -m tools.afip_final_integration start|stop|status|dashboard|research-once`
- canonical status: `runtime/final_integration_status.json`
- canonical dashboard: `runtime/dashboard/afip_dashboard.html`

No legacy module is deleted in this pack. Duplicate removal should occur only after long-run certification proves no caller depends on compatibility entry points.
