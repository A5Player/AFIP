# Production Milestone C Pack 7 — Market Knowledge Base Foundation

Pack 7 adds the first compact market knowledge base for AFIP. The goal is to preserve useful market experience without storing repeated raw data.

## Added

- `afip/knowledge/market_statistics_repository.py`
- `afip/knowledge/market_knowledge_repository.py`
- `afip/knowledge/market_pattern_repository.py`
- `afip/knowledge/market_snapshot_repository.py`
- `afip/knowledge/knowledge_quality.py`
- `afip/knowledge/knowledge_runtime.py`
- `afip/runtime/production_milestone_c_knowledge_runtime.py`
- `tests/test_production_milestone_c_pack_7.py`

## Capability

- Aggregates repeated market signatures into compact knowledge records.
- Stores occurrence count, win rate, expectancy, profit factor, MAE, MFE, and holding duration.
- Keeps selective lifecycle snapshots instead of storing every tick.
- Scores knowledge quality using sample confidence, freshness, and stability.
- Provides a production runtime for updating market knowledge from observation batches.

## Run

```powershell
pytest tests/test_production_milestone_c_pack_7.py -v

if ($LASTEXITCODE -ne 0) { exit }

pytest

if ($LASTEXITCODE -ne 0) { exit }

python tools/afip_local_quality_check.py

if ($LASTEXITCODE -ne 0) { exit }

git add .

git commit -m "Production Milestone C Pack 7"

git push
```
