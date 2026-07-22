New-Item -ItemType Directory -Force runtime\control | Out-Null
Set-Content runtime\control\stop_phase_v_major.flag "stop"
Write-Host "AFIP Phase V stop requested."
