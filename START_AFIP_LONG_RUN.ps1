$ErrorActionPreference = "Stop"
Remove-Item runtime\control\stop_phase_v_major.flag -ErrorAction SilentlyContinue
python -m tools.afip_phase_v_major run-forever
