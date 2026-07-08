# AFIP Walk-Forward Historical Paper Simulation

This document defines the Version 1 historical paper simulation standard for AFIP.

## Purpose

AFIP must evaluate historical data as if it is moving through time. The runtime may only use candles and market evidence available at the simulated decision point. Future candles must remain hidden until the next simulation step.

## Required standard

1. Load historical OHLC data in chronological order.
2. Reserve warmup bars for indicators and market context.
3. Evaluate only the visible window at each step.
4. Create a paper order decision when the runtime criteria are met.
5. Advance to the next bar before evaluating the outcome.
6. Record the decision, context, regime, spread condition, confidence, result, drawdown, and reason.
7. Build trading standards from the resulting distribution, not from future-known chart points.

## Look-ahead rule

Any simulation record that exposes future bars at decision time is blocked. This protects AFIP from look-ahead bias and prevents unrealistic standards.

## Production use

This pack does not send live orders. It creates the acceptance gate that will be used before automated adjustment from real trading results is allowed.
