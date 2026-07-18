# Technical Guide

Primary API: `KnowledgePortabilityEngine.build_manifest`, `verify_dataset`, `export_bundle`, `inspect_bundle`, and `import_bundle`. Manifests use schema `afip.knowledge.portability.v1`. Bundle paths are validated against absolute paths and `..` traversal. SHA-256 covers raw file bytes. Imports are immutable-by-default because an existing bundle destination is rejected.
