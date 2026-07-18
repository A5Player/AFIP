# Technical Guide

Use `DatasetRecord` for normalized metadata and `CentralDataCatalog` for validation,
registration, discovery, filtering, lineage checks, and deterministic snapshots.
Discovery is read-only and skips invalid metadata rather than modifying it.
