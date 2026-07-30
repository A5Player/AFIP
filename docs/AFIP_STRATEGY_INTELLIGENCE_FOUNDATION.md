# AFIP Strategy Intelligence Foundation — Milestone W Pack W3

W3 consumes W2 context-match evidence and ranks strategy templates for later plan review.

## Authority boundary

The engine is advisory only. It cannot create BUY/SELL orders, select lot size, set final SL/TP, bypass Capital/Risk/Execution gates, or call MT5.

## Fail-closed rules

A strategy remains `WAIT` when evidence count, sample size, similarity, or advisory score is insufficient. Passing W3 means only `ELIGIBLE_FOR_PLAN_REVIEW`; it is not permission to trade.

## Advisory score

The score combines weighted historical similarity, win rate, evidence quality and expectancy. W3 does not replace the OQS contract introduced in W1.
