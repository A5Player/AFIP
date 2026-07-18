$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone S Pack 7.1 ==="
python -m pytest -q tests/test_milestone_s_pack_7_1_position_ceiling_semantics.py tests/test_milestone_s_pack_5_5.py tests/test_milestone_s_cleanup_pack_4_2.py tests/test_milestone_s_pack_4.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Focused validation passed."
Write-Host "Run full regression with: python -m pytest -q"
