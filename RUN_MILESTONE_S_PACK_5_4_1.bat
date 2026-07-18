@echo off
setlocal

echo === AFIP Milestone S Pack 5.4.1 Validation ===
python -m pytest tests/test_milestone_s_pack_5_4_1.py tests/test_milestone_s_pack_5_4.py -q || exit /b 1
python tools/validate_financial_naming.py || exit /b 1
python tools/afip_mt5_multi_terminal_check.py --profiles P1 P2 P3 P4 --reconnect-attempts 2 || exit /b 1
echo Pack 5.4.1 validation completed.
endlocal
