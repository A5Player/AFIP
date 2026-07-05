# AFIP GitHub Workflow Guide

## Purpose

This document defines the official workflow for AFIP after the project has been moved to GitHub.

GitHub is now the source of truth for AFIP.

## Daily Workflow

### 1. Pull latest code

```bash
git pull
```

### 2. Run local quality check

```bash
python tools/afip_local_quality_check.py
```

This runs:

- Financial naming validation
- AFIP simulation
- MT5 data check
- Pytest

### 3. Make code changes

Add or update files for the current AFIP production batch.

### 4. Review changed files

```bash
git status
git diff
```

### 5. Commit

```bash
git add .
git commit -m "Production Batch 14: GitHub workflow and validation"
```

### 6. Push

```bash
git push
```

## Required Rules

- Use international financial terminology only.
- Do not use military terminology.
- Analytical components must use the Intelligence naming convention.
- Local validation must pass before push.
- GitHub Actions must pass after push.

## Local checks vs GitHub Actions

GitHub Actions runs on GitHub cloud and does not have the user's MT5 terminal.

Therefore:

- GitHub Actions validates naming, simulation, and tests.
- Local quality check validates naming, simulation, MT5 connection, and tests.

## Production Version Plan

- v0.1.0: Initial AFIP Production Architecture
- v0.2.0: Real MT5 Data Integration
- v0.3.0: Multi-Timeframe Confluence
- v0.4.0: Market Structure Intelligence
- v0.5.0: Liquidity Intelligence
- v0.6.0: Fair Value Gap Intelligence
- v0.7.0: Order Block Intelligence
- v0.8.0: Market Regime Intelligence
- v1.0.0: DEMO Ready
