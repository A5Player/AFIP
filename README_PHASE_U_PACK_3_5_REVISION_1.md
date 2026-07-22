# AFIP Phase U Pack 3.5 Revision 1

Packaging compatibility correction for the full-regression collection error.

The baseline ZIP contained `live_research_dashboard.py` outside the active `source/afip/dashboard_ui` package while the test imports `afip.dashboard_ui.live_research_dashboard`.

This revision places the existing module in the correct package path. It does not change Lot Authority, execution behavior, SL/TP, broker policy, credentials, or runtime data.
