# AFIP Version 1.0 Final Consolidation

This is the final large Patch Only integration authority built from uploaded AFIP(44).zip at commit `8bd57f9`. It establishes exactly two operational authorities: Trading Runtime and Research Runtime. It does not rewrite signal, risk, order, replay, data-lake or research algorithms.

Canonical operations: `START_AFIP.ps1`, `STOP_AFIP.ps1`, `STATUS_AFIP.ps1`. Canonical dashboard: `runtime/dashboard/afip_dashboard.html`. Canonical status: `runtime/final_integration_status.json`. Canonical research status: `runtime/research/research_engine_status.json`.

Legacy scripts remain compatibility-only to preserve backward compatibility; the architecture registry records them and prevents them from being treated as production authorities.
