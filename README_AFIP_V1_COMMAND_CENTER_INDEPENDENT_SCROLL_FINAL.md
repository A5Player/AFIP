# AFIP V1 Command Center Independent Scroll Final Repair

## Scope
Dashboard presentation and scrolling only. No trading, capital, lot, SL/TP, routing, MT5 initialization, or order-send logic is changed.

## Repair
- The Command Center shell is locked to the browser viewport.
- The left navigation has its own vertical scrollbar and bottom safe area.
- Each dashboard iframe has its own vertical scrollbar.
- Removes dynamic iframe-height JavaScript that caused clipping and f-string risk.
- Prevents lower dashboard content from being cut off by the browser or Windows taskbar.

## Validation
- Python compile: PASS
- Dashboard generation: PASS
- Full regression: 2734 passed
