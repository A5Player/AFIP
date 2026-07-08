# AFIP Rollback Guide

## Rollback Principle

Rollback should restore the last known good commit and configuration version without changing trading logic manually.

## Rollback Steps

1. Stop runtime execution.
2. Record the current commit and issue reason.
3. Checkout the previous known good commit.
4. Restore the matching configuration version.
5. Run validation commands.
6. Review production event logs and runtime metrics.
7. Resume only in simulation or paper mode first.

## Rollback Gate

Rollback is complete only when:

- Full pytest passes.
- Local quality check passes.
- MT5 check passes.
- Execution mode is confirmed safe.
- Operator records the rollback reason.
