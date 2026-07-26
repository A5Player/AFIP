# AFIP V1 Command Center F-string Syntax Repair

Repairs the Python f-string syntax error introduced by the single-scroll Command Center patch.

Scope:
- Correctly escapes JavaScript braces inside `afip/dashboard_ui/home.py`.
- Preserves single-scroll iframe resizing behavior.
- Preserves backward-compatibility markers required by earlier dashboard tests.
- No trading, execution, capital, lot, SL, TP, routing, or MT5 order-send logic changes.

Validation:
- Python compile: PASS
- Dashboard generation: PASS
- Full regression: 2731 passed
