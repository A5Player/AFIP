# Milestone I Pack 2 — News Intelligence

Transforms supplied news records into deterministic structured market intelligence for XM GOLD# paper/demo runtime.

## Features
- Category and gold-relevance classification
- Bullish, bearish, and neutral sentiment
- Source reliability score
- Normalized duplicate detection
- Reliability-weighted aggregate sentiment
- Dashboard explainability in English and Thai
- News cannot place orders or enable live execution

## Architecture
News data → classification → reliability/deduplication → structured market intelligence → later Market Regime V2. News never connects directly to execution.
