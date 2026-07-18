# Milestone S Pack 4.9 — Emergency Execution Safety

This fail-closed pack establishes the mandatory execution contract:

- `maximum_units` is a ceiling, never a forced target.
- Final units equal the minimum capacity approved by capital, confidence, risk,
  margin and remaining profile exposure.
- Missing adaptive protection blocks the order.
- The observed legacy TP 500 / SL 3000 fallback is explicitly rejected.
- SL source, TP source and planned holding horizon are mandatory.
- Profile identity remains metadata; account truth and config snapshots drive sizing.

Run the focused tests and source audit before restarting demo execution.
