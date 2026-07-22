# AFIP V1 Final Integration Regression Fix Pack

Purpose:
Fix final integration regressions without introducing new architecture.

Rules:
- Keep new Capital Authority lot policy.
- Do not restore legacy lot logic.
- Patch only failing integration contracts.
- Maintain backward compatibility where possible.

Scope:
- Capital authority regression alignment
- MT5 ownership safety validation
- Final integration contract alignment
- Dashboard contract alignment
- Legacy fixed lot protection
