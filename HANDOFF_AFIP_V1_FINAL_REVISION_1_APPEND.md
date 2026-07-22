## AFIP V1 Final Revision 1 Handoff

Run `RUN_AFIP_V1_FINAL_REVISION_1_COMPATIBILITY_CERTIFICATION.ps1` from the repository root.

Required before commit:

- Targeted tests pass
- Dashboard build passes
- Local quality passes
- Full regression passes with zero failures
- Review `git status`, `git diff --name-only`, and `git diff --cached --name-only`

Live execution remains operator-authorized only and must not be armed automatically.
