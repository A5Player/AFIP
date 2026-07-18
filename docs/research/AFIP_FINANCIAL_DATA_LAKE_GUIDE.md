# AFIP Financial Data Lake Guide

## Purpose
The Financial Data Lake stores reusable market evidence independently from P1-P4 presets. It is research infrastructure, not an execution engine.

## Layers
1. `raw`: source-faithful observations; append-only.
2. `normalized`: timestamps, symbols, fields and units normalized without changing economic meaning.
3. `derived`: features calculated from prior layers, always with a formula version.
4. `decision_context`: the exact information available when a decision was made.
5. `outcome`: post-decision observations linked to the original decision trace.

## No look-ahead
An event is eligible for a decision only when its availability timestamp is not later than the decision timestamp. Revisions are separate records; they never replace the originally available value.

## Traceability
Each record has a deterministic ID, provenance, quality metadata, research eligibility, checksum and partition manifest.

## Central dataset
Profiles are consumers of one central dataset. Profile names and presets are not primary research keys. Research segmentation uses market properties, pattern family, regime, session, timeframe, plan and formula versions.

## Safety
This module cannot send orders, arm execution or change execution locks.
