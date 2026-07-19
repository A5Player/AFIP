param([int]$IntervalSeconds=300)
$ErrorActionPreference='Stop'; Set-Location $PSScriptRoot
Remove-Item runtime\control\stop_cross_market_research.flag -ErrorAction SilentlyContinue
python tools/afip_phase_u_pack_3_4_10_collector.py --root . --interval-seconds $IntervalSeconds
exit $LASTEXITCODE
