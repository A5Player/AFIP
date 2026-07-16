$ErrorActionPreference = "Stop"
python -m pytest tests\test_milestone_s_pack_5_4.py -v
python -m pytest
python tools\afip_local_quality_check.py
python -m afip.dashboard_ui
