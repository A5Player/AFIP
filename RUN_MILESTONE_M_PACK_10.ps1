$ErrorActionPreference = "Stop"
pytest tests/test_milestone_m_pack_10.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
