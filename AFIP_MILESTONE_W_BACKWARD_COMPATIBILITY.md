# Milestone W Backward Compatibility

Pack W0 changes no trading behavior. Existing runtime files, launch scripts, schemas and compatibility modules remain untouched. Future packs must use additive schema versions, tolerant readers and deterministic adapters. No legacy field may override Capital, Risk, Intelligence or Execution authority. Rollback consists of removing the additive Milestone W files.
