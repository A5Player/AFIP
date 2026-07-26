# AFIP V1 Control Center & Research Presentation Completion

Patch-only dashboard presentation repair.

Changes:
- AFIP V1 Control Center uses four fixed comparison columns on desktop.
- Automatic Research Runtime uses compact typography and no internal vertical scrollbar.
- Data Loading & Research Operations replaces mojibake text with valid UTF-8 symbols and punctuation.
- No trading, execution, sizing, capital, SL, TP, routing, or order-send logic is changed.

Install by copying the pack contents over `C:\AFIP`.

Validation:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
python -m pytest
python -m afip.dashboard_ui
Start-Process C:\AFIP\runtime\dashboard\afip_dashboard.html
```

Expected regression result: `2737 passed`.
