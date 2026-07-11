# AFIP Milestone Q Pack 1 — Market Intent Intelligence Foundation

## Purpose

This patch establishes the immutable, deterministic research foundation for Market Intent Intelligence. It converts certified Market Regime and Market Behaviour evidence into a normalized intent observation only after both required evaluations have completed.

## Intent states

- BUYING_PRESSURE
- SELLING_PRESSURE
- LIQUIDITY_SEEKING
- BREAKOUT_ATTEMPT
- REVERSAL_ATTEMPT
- BALANCED_INTENT

## Safety controls

The runtime blocks observations when data quality, chronology, future safety, Market Regime ordering, Market Behaviour ordering, metric ranges, broker/symbol/base-unit policy, or the frozen execution policy fails.

It cannot update parameters, change trading logic, promote production knowledge, modify positions, contact a broker, or transmit orders.

## Validation

Run the commands in `VALIDATION_MILESTONE_Q_PACK_1.md` after extracting the patch over the repository root.

## Install

Extract this patch over the AFIP repository root. Do not replace the repository and do not remove unrelated files.
