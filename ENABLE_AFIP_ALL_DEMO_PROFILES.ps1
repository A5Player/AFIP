$ErrorActionPreference = "Stop"
$configPath = Resolve-Path ".\config\four_profile_demo.json"
$config = Get-Content $configPath -Raw | ConvertFrom-Json
foreach ($profile in $config.profiles) {
    $profile.enabled = $true
    $profile.demo_execution_enabled = $true
}
$json = $config | ConvertTo-Json -Depth 30
[System.IO.File]::WriteAllText($configPath, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "P1-P4 enabled for AFIP demo operation. Demo order transmission still requires local arming."
