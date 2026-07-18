$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 5 ==="
Write-Host "Exit Experiment Aggregation, Context Segmentation & Evidence Evaluation"
python -m pytest -q tests/test_milestone_t_pack_5_exit_evidence_research.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Milestone T Pack 5 validation completed."
