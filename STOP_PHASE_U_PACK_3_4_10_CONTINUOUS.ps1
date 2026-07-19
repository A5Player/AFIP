New-Item -ItemType Directory -Force runtime\control | Out-Null
New-Item -ItemType File -Force runtime\control\stop_cross_market_research.flag | Out-Null
Write-Host 'Stop flag created. Collector stops after the current cycle.'
