# AFIP Dashboard Foundation

Milestone H starts the AFIP Dashboard Center. The purpose is to make AFIP easy to inspect before and during production trials.

## Primary dashboard groups

1. Executive Summary
2. Intelligence Center
3. Engine Center
4. Trading Center
5. Walk-Forward Center
6. Experience Center
7. Top 10 Center
8. AFIP Bank / Capital Summary
9. Runtime Metrics
10. System Health

## Intelligence and engine cards

Each card should show:

- Status icon
- English name
- Thai name
- Function
- Explanation
- Input summary
- Output summary
- Confidence or health state
- Dependency summary where applicable

## Top 10 Center

The Top 10 Center will rank historical and trial results such as:

- Best trading hours
- Best sessions
- Best market regimes
- Best trading patterns
- Best intelligence combinations
- Best confidence ranges
- Best no-trade reasons
- Most common loss causes
- Best risk settings
- Best account conditions

## Production rule

This dashboard layer is presentation-only. It must not change trading decisions, risk controls, execution behavior, or learning standards.
