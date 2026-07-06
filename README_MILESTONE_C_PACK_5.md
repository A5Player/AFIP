# AFIP Production Milestone C Pack 5

## Macro Market Consensus Integration

Pack 5 integrates the Milestone C macro components into one financial consensus layer.
It combines economic calendar risk, macro event impact, macro news confidence, and macro market factor bias into a single market-aware exposure profile.

## Added

- Integrated macro market consensus engine
- Macro market decision profile engine
- Production consensus runtime wrapper
- Calendar + news + market factor integration tests
- Pack run scripts
- Project database updates

## Financial behavior

The runtime produces:

- `macro_score`
- `decision_confidence`
- `gold_market_bias`
- `conflict_level`
- `exposure_instruction`
- `position_horizon`
- `review_required`

## Safety and design

- Restricted high-impact calendar windows still prevent new exposure.
- Conflicting macro inputs route to review-only conditions.
- The architecture remains provider-neutral and ready for free or paid data adapters.
- No non-financial naming is introduced.

## Run

```powershell
pytest tests/test_production_milestone_c_pack_5.py -v

if ($LASTEXITCODE -ne 0) { exit }

pytest

if ($LASTEXITCODE -ne 0) { exit }

python tools/afip_local_quality_check.py

if ($LASTEXITCODE -ne 0) { exit }

git add .

git commit -m "Production Milestone C Pack 5"

git push
```
