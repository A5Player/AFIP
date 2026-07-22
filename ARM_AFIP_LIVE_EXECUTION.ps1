param([Parameter(Mandatory=$true)][string]$Confirmation)
python -m tools.afip_phase_v_major arm-live --confirmation $Confirmation
