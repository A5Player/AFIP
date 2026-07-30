# AFIP Milestone W Pack W15 — Dashboard Runtime Integration

W15 combines the W11–W14 foundations into one read-only runtime pipeline:

Snapshot
→ Read Model
→ Presentation Model
→ Panel Adapter
→ Dashboard Context

The bridge preserves existing dashboard context keys and adds:

- advisory_intelligence
- advisory_runtime_status
- advisory_runtime_reason
- advisory_display_ready

This pack does not modify HTML templates and does not write execution state.
