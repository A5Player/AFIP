$ErrorActionPreference='Stop'; Set-Location $PSScriptRoot
python -c "from afip.dashboard_ui.research_operations import write_research_operations_dashboard; print(write_research_operations_dashboard('runtime/dashboard','.'))"
