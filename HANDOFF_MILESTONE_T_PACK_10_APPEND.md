## Milestone T Pack 10 Handoff

Pack 10 adds adaptive multi-objective plan ranking.

Hard gates:

- Maximum drawdown
- Risk of ruin
- Losing streak
- Tail loss
- Capital survival
- Minimum sample size
- Walk-forward score
- Robustness score
- Data quality score

Only plans passing both capital and evidence gates can be selected. Context match is evaluated before the adaptive composite score. P1-P4 use separate profile weights. Context changes may adjust weights within a bounded range.

Dashboard contract stores Top 10, expandable Top 100 and hidden counts with pattern and situation names.

Next recommended pack: real MT5 historical gateway and multi-instrument backfill runner, while wiring selected ranking IDs into runtime decision traces.
