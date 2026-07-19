param(
    [int]$CollectorTimeoutSeconds = 900,
    [int]$DashboardTimeoutSeconds = 180,
    [switch]$SkipTests
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host 'AFIP Phase U Final Integration - bounded one-shot research run'
Write-Host 'Real data only. Research only. No execution authority.'

$arguments = @(
    'tools/afip_phase_u_final_research.py',
    '--collector-timeout', $CollectorTimeoutSeconds,
    '--dashboard-timeout', $DashboardTimeoutSeconds
)
if ($SkipTests) { $arguments += '--skip-tests' }

python @arguments
if ($LASTEXITCODE -ne 0) {
    Write-Error "AFIP final research finished with a non-pass result. Review runtime\research\final_research_run.json"
    exit $LASTEXITCODE
}

Write-Host 'AFIP final one-shot research completed successfully.'
Write-Host 'Report: runtime\research\final_research_run.json'
Write-Host 'Dashboard: runtime\dashboard\afip_dashboard.html'
