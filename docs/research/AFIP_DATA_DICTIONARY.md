# AFIP Data Dictionary Guide

The canonical machine-readable dictionary is `config/research_data/data_dictionary.json`.

Each field definition must include:

- `field_id`: stable, namespaced identifier.
- `meaning`: precise financial or operational meaning.
- `data_type`: storage and validation type.
- `source`: original system, feed, or derivation.
- `unit`: points, price, currency, percentage, category, or UTC time.
- `quality_rules`: checks required before research use.
- `lineage`: raw/normalized/derived/decision/outcome layer and transform.

Field identifiers remain stable. Meaningful semantic changes require a new field or dictionary version. Profile names and presets must not be embedded in core research field identifiers.
