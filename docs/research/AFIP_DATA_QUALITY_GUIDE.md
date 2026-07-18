# AFIP Data Quality Guide

AFIP evaluates freshness, completeness, timestamp alignment, source reliability, and cross-source agreement. Status values are `PASS`, `CAUTION`, `BLOCK`, and `UNKNOWN`.

`BLOCK` or `UNKNOWN` on required decision data prevents research eligibility. A quality failure does not delete the record; it marks it for quarantine and preserves evidence for incident analysis.
