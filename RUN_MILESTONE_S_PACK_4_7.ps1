$ErrorActionPreference = "Stop"
pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_7.py
pytest
python tools\afip_local_quality_check.py
