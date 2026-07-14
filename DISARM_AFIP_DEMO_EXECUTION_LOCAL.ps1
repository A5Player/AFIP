$ErrorActionPreference = "Stop"
[Environment]::SetEnvironmentVariable("AFIP_DEMO_EXECUTION_ARMED", "NO", "User")
foreach ($profile in @("P1","P2","P3","P4")) {
    [Environment]::SetEnvironmentVariable("AFIP_${profile}_DEMO_ARMED", "NO", "User")
}
Write-Host "AFIP demo execution disarmed. Stop demo workers and reopen PowerShell."
