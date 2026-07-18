# AFIP Score Calculation Guide

Calculation order:

1. Validate source identity, timestamps, symbol, and freshness.
2. Preserve raw component values.
3. Normalize units without overwriting raw values.
4. Calculate component scores with registered formulas.
5. Calculate composite scores and explicit penalties.
6. Evaluate hard gates independently.
7. Commit the decision and complete Decision Trace.

A score record must retain input values, component statuses, weights, penalties, formula ID/version, calculation timestamp, and quality status. Future versions can recompute derived scores from immutable raw observations while preserving the original result.
