$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.2.2 - Stale Replay Checkpoint Recovery"
python -m pytest tests/test_phase_u_pack_3_2_2_stale_replay_checkpoint_recovery.py tests/test_phase_u_pack_3_2_1_visible_research_pipeline.py -q
if ($LASTEXITCODE -ne 0) { throw "Pack 3.2.2 tests failed." }
Write-Host ""
Write-Host "Running visible research pipeline..."
python -u afip.py research-bootstrap
if ($LASTEXITCODE -ne 0) { throw "Research bootstrap failed." }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed." }
Write-Host "PASS - stale replay checkpoints recover without deleting research history."
Start-Process ".\runtime\dashboard\afip_research_data_dashboard.html"
