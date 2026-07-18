# AFIP Decision Trace Guide

Every evaluated opportunity requires a trace containing:

- trace ID and UTC observation timestamp;
- dictionary and formula versions;
- market regime and complete market context;
- component scores, composite scores, and penalties;
- every gate with status, reason, input, and limit;
- requested and approved units/lots;
- final decision and execution result;
- source timestamps and data-quality status;
- research eligibility classification and reasons.

A `NO_ORDER` decision is a first-class research record and must be traceable to the first blocking gate.
