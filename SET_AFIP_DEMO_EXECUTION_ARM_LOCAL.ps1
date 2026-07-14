$ErrorActionPreference = "Stop"
Write-Host "AFIP DEMO execution arming"
Write-Host "This enables broker order transmission ONLY after AFIP verifies MT5 trade_mode=DEMO."
$confirmation = Read-Host "Type exactly: ARM DEMO P1-P4"
if ($confirmation -cne "ARM DEMO P1-P4") {
    throw "Demo execution was not armed. Confirmation text did not match."
}
[Environment]::SetEnvironmentVariable("AFIP_DEMO_EXECUTION_ARMED", "YES", "User")
foreach ($profile in @("P1","P2","P3","P4")) {
    [Environment]::SetEnvironmentVariable("AFIP_${profile}_DEMO_ARMED", "YES", "User")
}
Write-Host "Demo execution arm saved for P1-P4. Close and reopen PowerShell before use."
