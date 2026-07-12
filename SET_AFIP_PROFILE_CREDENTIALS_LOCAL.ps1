$ErrorActionPreference = "Stop"
Write-Host "AFIP local credential setup (credentials are stored in Windows user environment only)."
foreach ($Profile in 1..4) {
    $Login = Read-Host "P$Profile MT5 login"
    $SecurePassword = Read-Host "P$Profile MT5 password" -AsSecureString
    $Pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
    try { $Password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Pointer) }
    [Environment]::SetEnvironmentVariable("AFIP_P${Profile}_LOGIN", $Login, "User")
    [Environment]::SetEnvironmentVariable("AFIP_P${Profile}_PASSWORD", $Password, "User")
    Remove-Variable Password
}
Write-Host "Credential environment variables saved. Close and reopen PowerShell before starting AFIP."
