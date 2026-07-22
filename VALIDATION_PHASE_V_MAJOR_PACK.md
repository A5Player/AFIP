# Validation

Targeted pack tests expected: 8 passed.

Run:
1. `python -m pytest tests/test_phase_v_major_pack.py -q`
2. `python -m tools.afip_phase_v_major run-once`
3. Review `runtime/research/phase_v_major_status.json`
4. Run related historical/research/dashboard tests
5. Run `python -m pytest`
6. Review git diff, commit, push, and confirm GitHub Actions

Do not claim production or live readiness until the user's machine returns the actual results.
