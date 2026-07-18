$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone S Pack 4.9 Emergency Execution Safety ==="

python -m pytest tests\test_milestone_s_pack_4_9_emergency_execution_safety.py -v
python tools\afip_pack_4_9_source_audit.py

Write-Host ""
Write-Host "IMPORTANT:"
Write-Host "1. Do not restart demo execution until the source audit is reviewed."
Write-Host "2. The guard is fail-closed and rejects legacy TP 500 / SL 3000 fallback."
Write-Host "3. Wire approve_execution() directly before MT5 order_check/order_send."
