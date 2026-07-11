# AFIP Milestone P Pack 1 — Market Behaviour Intelligence Foundation

## Purpose

This patch establishes the immutable, deterministic research foundation for Market Behaviour Intelligence. It converts certified market measurements into a normalized behaviour observation only after Market Regime has been evaluated.

## Behaviour states

- DIRECTIONAL_PERSISTENCE
- RANGE_ROTATION
- REGIME_TRANSITION
- VOLATILITY_EXPANSION
- VOLATILITY_COMPRESSION
- BALANCED_BEHAVIOUR

## Safety controls

The runtime blocks observations when data quality, chronology, future safety, regime-first sequencing, metric ranges, broker/symbol/base-unit policy, or the frozen execution policy fails.

It cannot update parameters, change trading logic, promote production knowledge, modify positions, contact a broker, or transmit orders.

## Validation

- Targeted tests: 8 passed
- Full test suite: 1503 passed
- AFIP Local Quality Check: PASS
- Dashboard generation: PASS

## Install

Extract this patch over the AFIP repository root. Do not replace the repository and do not remove unrelated files.
