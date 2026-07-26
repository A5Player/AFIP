# Runtime Truth Source Audit

## Repository examined
Supplied `AFIP(63).zip`, extracted repository root `AFIP/`.

## Git state observation
The supplied repository reported thousands of modified files. The diff pattern is consistent with widespread content/line-ending transformation and was not treated as part of this patch. Only the six files listed in this pack are modified/copied.

## Runtime truth sources found
- `afip/runtime_truth.py` — authoritative process/session/financial/runtime/operational presentation truth.
- `afip/dashboard_state_machine.py` — current-vs-historical dashboard state compatibility layer.
- `afip/dashboard_data_contract.py` — read-only evidence collection and atomic dashboard snapshot.
- `afip/dashboard_operations_health.py` — operations explanation and summary.
- `afip/dashboard_ui/authority_snapshot.py` — dashboard consumer bridge.
- `afip/dashboard_ui/split_runtime.py` — P1–P4 renderer.
- `afip/live_mt5_dashboard.py` — live/passive evidence renderer.
- `afip/execution_pipeline_dashboard.py` and `afip/order_evidence_dashboard.py` — execution/order evidence consumers.

## Confirmed root cause
`dashboard_data_contract.py` attached `operations_health` before `authoritative_runtime_truth`. Therefore Operations could calculate from the older state-machine model while renderers later displayed fields overwritten by the authoritative model. This generated internally inconsistent counters and per-profile labels.

## Repair
- Attach authoritative runtime truth before operations-health calculation.
- Make operations health consume `authoritative_runtime_truth` first and use legacy truth only as fallback.
- Restore a backward-compatible per-terminal process seam while retaining read-only executable-path detection.
- Preserve old `session_state=NOT_VERIFIED_PASSIVE` for compatibility and add canonical `broker_session_state=NOT_VERIFIED`.
- Preserve snapshots as `LAST_SNAPSHOT`, never `LIVE` in passive mode.
- Mark observation current only when process evidence is actually present (`process_alive is not None`).
