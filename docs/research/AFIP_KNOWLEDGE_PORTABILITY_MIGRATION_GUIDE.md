# Migration Guide

Pack 6.3 does not transform payload schemas. It preserves files exactly. When a future schema differs, import into isolation, run a separately versioned migration, retain the original bundle, produce a new manifest, and record parent bundle ID plus migration tool version. Never mutate the original portable bundle.
