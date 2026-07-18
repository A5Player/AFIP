# AFIP Milestone S Cleanup Pack 4.2

## Purpose

Repair the two residual full-regression failures after Cleanup Pack 4.1 without weakening P1-P3 demo execution policy.

## Changes

1. Replaces the non-financial documentation term `Protection Control` with `Protection Control`.
2. Restores the historical risk-approved simulation contract for Confidence Calibration.
3. Keeps the normal P1-P3 confidence maximum-unit policy unchanged:
   - below 98.00: 0 normal execution units
   - 98.00-98.49: maximum 1 unit
   - 98.50-99.49: maximum 2 units
   - 99.50-100.00: maximum 3 units
4. Allows exactly one compatibility unit only for the explicitly marked legacy `SIMULATION` path after RiskAssessor approval.
5. Risk failure, excessive spread, WAIT decisions, and direct builder calls remain fail-closed.
6. Records unit-allocation source in the simulation order.
7. Removes `patch_payload` after installation to prevent pytest import-file mismatch.

Execution remains stopped after installation.

