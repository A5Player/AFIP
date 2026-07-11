# AFIP Milestone Q Pack 2 — Market Intent State Normalization

## Purpose

This patch normalizes accepted Milestone Q Pack 1 Market Intent observations into one deterministic, immutable, canonical research schema.

## Normalized outputs

- Canonical intent state and direction
- Dominant pressure
- Intent intensity and intensity band
- Continuation-versus-reversal balance
- Directional alignment
- Source lineage and chronology

## Safety controls

Normalization requires valid Pack 1 lineage, certified data, future-safe chronology, Market Regime before Intent, Market Behaviour before Intent, valid labels and metric ranges, XM Only, GOLD# Only, and the frozen execution policy.

It cannot update parameters, change trading logic, promote production knowledge, modify positions, contact a broker, or transmit orders.

## Install

Extract this patch over the AFIP repository root. Do not replace the repository and do not remove unrelated files.

## Validation

Run `RUN_MILESTONE_Q_PACK_2.ps1` or `RUN_MILESTONE_Q_PACK_2.bat`.
