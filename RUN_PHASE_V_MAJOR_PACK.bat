@echo off
python -m pytest tests/test_phase_v_major_pack.py -q || exit /b 1
python -m tools.afip_phase_v_major run-once || exit /b 1
