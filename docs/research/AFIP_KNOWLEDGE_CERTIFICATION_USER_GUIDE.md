# User Guide — Knowledge Certification

1. Place validated evidence from Pack 6.1 into a research workflow.
2. Load `config/knowledge_certification/certification_policy.json`.
3. Run `KnowledgeCertificationFramework.certify(...)` with a named reviewer.
4. Store the returned certification in `data/knowledge/certification/registry/` or an append-only JSONL ledger.
5. Store `lineage_record(...)` in `data/knowledge/certification/lineage/`.
6. Interpret `RESEARCH_CERTIFIED` as research approval only, never permission to trade.
