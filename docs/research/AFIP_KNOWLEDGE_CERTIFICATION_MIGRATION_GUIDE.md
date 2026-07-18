# Migration Guide — Knowledge Certification

Schema `1.0.0` is the initial version. Future schema changes must:

1. retain original records unchanged;
2. create a versioned migration script;
3. write migrated output to a new dataset/version location;
4. preserve source IDs and add migration provenance;
5. update `dataset_info.json` and the data dictionary;
6. validate record counts and deterministic hashes before adoption.
