# AFIP Milestone S Pack 4.6

Capital Growth Table Safety Correction.

P1 and P2 use explicit configuration tables rather than a linear capital formula. The final risk ceiling is four concurrent orders at 0.03 lot each. Account balance above the final tier does not increase order size.

P1 final tier: USD 7,200 -> 0.03, 0.03, 0.03, 0.03.
P2 final tier: USD 7,800 -> 0.03, 0.03, 0.03, 0.03.

P3/P4 remain research profiles using one fixed 0.01 order for each approved distinct signal. Confidence, risk, spread, margin, cooldown, demo verification, arming, and manual-position override remain enforced.
