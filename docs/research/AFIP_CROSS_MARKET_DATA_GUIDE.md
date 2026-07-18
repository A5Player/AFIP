# AFIP Cross-Market Data Guide

Cross-market context must be timestamp-aligned to the gold decision timestamp. Candidate domains include USD indexes and pairs, sovereign yields, bonds, oil, volatility indexes, equity indexes, commodities, ETFs, positioning, macro releases, central-bank events, liquidity, and news.

Each source records provider, instrument, native timestamp, received timestamp, normalization rule, market-hours status, freshness limit, and missing-data reason. Missing cross-market data must never be silently converted to neutral evidence.
