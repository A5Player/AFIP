# AFIP V1 Command Center Single-Scroll Final Repair

This patch removes the nested iframe scrollbar from the Command Center.
The parent page now resizes the embedded dashboard to its full document height
and uses one browser scrollbar for the entire page. The lower safe area remains
visible above the Windows taskbar.

Scope: dashboard presentation only. No trading or execution authority changes.
