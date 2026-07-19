# Git Commands — Phase U Final Integration

Run only after validation and the one-shot research command complete.

```powershell
cd C:\AFIP
git status --short

git add .gitignore pytest.ini `
  afip/afip_bank_live/runtime.py `
  afip/dashboard_ui/__main__.py afip/dashboard_ui/launcher.py afip/dashboard_ui/home.py afip/dashboard_ui/cross_market.py `
  afip/financial_intelligence_certification afip/cross_market_gold_intelligence afip/continuous_research_runtime `
  config/cross_market_gold_intelligence.json config/continuous_research_runtime.json `
  tools/afip_phase_u_pack_3_4_9_runtime.py tools/afip_phase_u_pack_3_4_10_collector.py tools/afip_phase_u_final_research.py `
  tests/test_phase_u_pack_3_4_9.py tests/test_phase_u_pack_3_4_10.py tests/test_phase_u_final_research.py `
  RUN_PHASE_U_PACK_3_4_9.ps1 RUN_PHASE_U_PACK_3_4_9.bat VALIDATE_PHASE_U_PACK_3_4_9.ps1 `
  RUN_PHASE_U_PACK_3_4_10_ONCE.ps1 START_PHASE_U_PACK_3_4_10_CONTINUOUS.ps1 STOP_PHASE_U_PACK_3_4_10_CONTINUOUS.ps1 `
  RUN_AFIP_FINAL_RESEARCH.ps1 RUN_AFIP_FINAL_RESEARCH.bat VALIDATE_PHASE_U_FINAL.ps1 `
  README_PHASE_U_PACK_3_4_9.md README_PHASE_U_PACK_3_4_9_TH.md README_PHASE_U_PACK_3_4_10.md README_PHASE_U_PACK_3_4_10_TH.md `
  README_PHASE_U_FINAL_INTEGRATION.md README_PHASE_U_FINAL_INTEGRATION_TH.md `
  FILE_LIST_PHASE_U_PACK_3_4_9.md FILE_LIST_PHASE_U_PACK_3_4_10.md FILE_LIST_PHASE_U_FINAL_INTEGRATION.md `
  VALIDATION_GUIDE_PHASE_U_PACK_3_4_9.md VALIDATION_GUIDE_PHASE_U_PACK_3_4_10.md VALIDATION_GUIDE_PHASE_U_FINAL_INTEGRATION.md `
  GIT_COMMANDS_PHASE_U_PACK_3_4_9.md GIT_COMMANDS_PHASE_U_PACK_3_4_10.md GIT_COMMANDS_PHASE_U_FINAL_INTEGRATION.md `
  HANDOFF.md HANDOFF_PHASE_U_PACK_3_4_9_APPEND.md HANDOFF_PHASE_U_PACK_3_4_10_APPEND.md HANDOFF_PHASE_U_FINAL_INTEGRATION_APPEND.md `
  AFIP_PROJECT_DATABASE.md AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_4_9_APPEND.md AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_4_10_APPEND.md AFIP_PROJECT_DATABASE_PHASE_U_FINAL_INTEGRATION_APPEND.md

git status --short
git commit -m "Complete Phase U final research runtime integration"
git push origin main
```

Do not stage `runtime/research`, generated dashboard HTML, `.venv`, backup, or PATCH runtime artifacts unless intentionally required.
