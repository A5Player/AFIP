# CHANGELOG

## Production Batch 14.1 — Pytest Legacy Import Fix

- Fixed legacy `aif` import in `tests/phase2/test_afip_intelligence_naming.py`.
- Aligned phase2 naming test with official AFIP financial naming standard.
- Added regression coverage to keep removed legacy package references out of the test suite.
