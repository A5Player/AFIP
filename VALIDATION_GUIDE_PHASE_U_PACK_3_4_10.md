# Validation
1. `python -m pytest tests/test_phase_u_pack_3_4_10.py`
2. `python tools/afip_phase_u_pack_3_4_10_collector.py --root . --once`
3. Confirm:
   - `runtime/research/cross_market/latest.json`
   - `runtime/research/cross_market/observations.jsonl`
   - `runtime/research/cross_market/evidence.json`
   - `runtime/research/cross_market/collector_status.json`
4. `python tools/afip_local_quality_check.py`
5. `python -m pytest`
