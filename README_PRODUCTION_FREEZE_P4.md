# Production Freeze P4 — Deployment & Operations

This patch adds a deterministic deployment and operations readiness layer. It documents VPS deployment, MT5 preparation, startup expectations, backup, restore, rollback, and operating checks.

## Scope

- Deployment readiness model.
- Operations readiness report.
- VPS and MT5 deployment guide.
- Daily, weekly, and monthly operations checklist.
- Backup and restore guide.
- Rollback guide.
- Deterministic tests.

## Safety

P4 does not alter trading decisions, execution logic, strategy logic, lot sizing, or risk rules. It blocks live execution mode in the readiness review and remains compatible with the existing simulation-only production controls.
