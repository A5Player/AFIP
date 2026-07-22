param([int]$IntervalSeconds=300,[int]$MaximumReplayBars=5000)
$ErrorActionPreference='Stop'; Set-Location $PSScriptRoot
Remove-Item runtime\control\stop_cross_market_research.flag -ErrorAction SilentlyContinue
Write-Host 'AFIP Unified Continuous Research: MT5 M1-D1 -> Data Lake -> Replay -> Cross-market -> Dashboard 4'
Write-Host 'Research only. execution_authority=false. order_send_called=false.'
python tools/afip_phase_u_pack_3_4_10_collector.py --root . --interval-seconds $IntervalSeconds --maximum-replay-bars $MaximumReplayBars
exit $LASTEXITCODE
