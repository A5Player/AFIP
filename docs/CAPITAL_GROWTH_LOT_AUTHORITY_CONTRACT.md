# Capital Growth Lot Authority Contract

Final calculation order:

Signal
-> Confidence Authority
-> Profile Capital Tier
-> Lot Allocation Authority
-> Margin Authority
-> Exposure Authority
-> Risk Authority
-> Final Approved Units

Legacy fixed 0.01 x 3 logic must not bypass this flow.

Confidence:
<98.0 = 0 units
98.0-98.49 = max 1 unit
98.5-99.49 = max 2 units
99.5-100 = max 3 units
