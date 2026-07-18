
## Milestone T Pack 5 — Exit Experiment Aggregation, Context Segmentation & Evidence Evaluation

### Architecture

- Adds a research-only evidence layer above Pack 4 position outcomes.
- Aggregates outcomes by exit policy and deterministic market-context segment.
- Records sample size, win rate, average/median/worst/best realized R, dispersion, exit quality, capital preservation, profit capture, adverse excursion, holding period, consistency, and evidence score.
- Evaluates research evidence eligibility without Production promotion.
- Compares policies only within a shared context segment and never selects a winner.

### Research Datasets

- `exit_evidence_observations`
- `exit_context_segments`
- `exit_evidence_summaries`
- `exit_evidence_evaluations`
- `exit_policy_comparisons`

### Safety

- Research state remains `EXPERIMENTAL`.
- Production usability remains false.
- Automatic promotion is prohibited.
- Production Runtime and Trading Logic are unchanged.
- No MT5 execution action is present.
