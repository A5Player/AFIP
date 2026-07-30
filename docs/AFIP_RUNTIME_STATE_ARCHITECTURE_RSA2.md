# AFIP Runtime State Architecture — RSA-2

RSA-2 converts the RSA-1 classification report into a formal persistence, retention, Git, backup, and archive policy matrix.

## Safety

This pack is report-only. It never moves, deletes, restores, untracks, archives, or changes `.gitignore`.

## Input

`runtime/control/runtime_state_architecture/rsa1/runtime_classification.json`

## Outputs

- `runtime/control/runtime_state_architecture/rsa2/runtime_persistence_policy.json`
- `runtime/control/runtime_state_architecture/rsa2/runtime_persistence_policy.md`

UNCLASSIFIED files remain explicit blockers for automatic RSA-3 refactoring.
