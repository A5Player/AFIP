# AFIP V1 Final Revision 1 — Compatibility Certification

Patch-only certification revision for the final AFIP V1 runtime observatory pack.

## Scope

- Restore `margin_free` and `profit` compatibility fields while retaining the canonical `free_margin` and `floating_profit` fields.
- Preserve both existing Dashboard spread contracts required by current regression suites.
- Publish explicit research-only metadata on Dashboard 4:
  - `execution_authority=false`
  - `order_send_called=false`
- Remove obsolete capital-per-0.01 and tier presentation from Dashboard profile rows.
- Do not change lot authority, execution authority, profile risk rules, replay behavior, or live arming.

## Safety

- Patch Only
- Backward Compatible
- Dashboard remains read-only
- Research has no execution authority
- Live execution is never armed automatically
