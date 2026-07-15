# Validation Guide — Milestone S Pack 5.1

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "C:\AFIP"

.\RUN_MILESTONE_S_PACK_5_1.ps1
```

## Controlled local ingestion

```powershell
python tools\afip_research_recorder.py ingest-ledger `
  runtime\profiles\p4\logs\demo_execution_ledger.jsonl `
  --output runtime\research

python tools\afip_research_recorder.py status --output runtime\research
```

Expected outputs:
- `runtime/research/events/research_events.jsonl`
- `runtime/research/trade_cases/CASE-*.json`
- `runtime/research/research_index.json`

This command is read-only toward trading and may be run while demo execution is stopped or running.
