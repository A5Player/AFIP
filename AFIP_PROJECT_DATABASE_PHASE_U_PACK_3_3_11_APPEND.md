
## Phase U Pack 3.3.11 — Runtime Research Data Git Isolation

Status: IMPLEMENTED; validation pending on user repository.

- Runtime-generated automatic research streams are isolated from Git.
- Historical data lake, checkpoints, exports, and quarantine datasets are local/VPS research assets.
- Five previously tracked schema-v2 JSONL streams are removed from the Git index without deleting local files.
- Source code, configuration, tests, documentation, and required fixtures remain version controlled.
- No trading logic, execution permission, risk, lot, SL, TP, or profile behavior is changed.
- This pack is a prerequisite for large-scale historical research and Top 10 / Top 100 ranking work.
