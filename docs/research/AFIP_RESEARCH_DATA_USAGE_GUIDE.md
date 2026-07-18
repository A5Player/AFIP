# AFIP Research Data Usage Guide

Only `RESEARCH_ELIGIBLE` records may feed rankings, calibration, or future model training. `QUARANTINED` records are retained for diagnosis but excluded from performance claims. `INCIDENT_REFERENCE_ONLY` records document faults and recovery behavior.

Eligibility is denied when look-ahead is detected, an execution/configuration incident affected the sample, or required data quality is unacceptable. A later manual review may create a new classification event; it must not overwrite the original classification.
