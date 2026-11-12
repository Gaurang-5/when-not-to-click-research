# Safe visual grounding with Jev 1.14

This package evaluates whether Jev 1.14's native presence, none/one/several Choice and Box outputs can support click-or-abstain decisions for absent and ambiguous GUI targets.

## Result

The 200-call real Jev pilot is complete. On 80 held-out synthetic cases:

- Box confidence accepted 27 cases with 10 incorrect clicks.
- Presence + uniqueness + Box accepted 26 with zero incorrect clicks.
- A logistic joint gate accepted 29 with zero incorrect clicks.
- Uniqueness-only accepted all 30 eligible unique targets and no negative case.
- The D-versus-B multiple-target difference was −50 percentage points, with Holm-adjusted p=0.126.
- All policies rejected the ten absent cases.

The result supports Jev's native match-count signal on this controlled dataset. It does not establish real-world safety, and it does not show that combining all three signals is better than using Choice alone.

## Execution

- 200 requests, 199 valid outputs, one fail-closed degenerate Box.
- Every response resolved to `jev-1.14.0`.
- 457,978 input tokens; estimated total cost **$0.019235**.
- Test latency: 524 ms mean and 647 ms p95.
- 55 tests pass.
- Frozen-policy SHA-256: `ad4e7cdecd3a8add7dd4ac091d960085cafb0cf171ed7edb5e3706a5c4e5ca94`.

## Reproduce analysis

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/evaluate_live.py
```

`evaluate_live.py` verifies the frozen-policy hash and requires all 80 held-out cases. It never refits thresholds. `freeze_live_policy.py` refuses to run after test outputs exist.

## Navigation

- `reports/FINAL_REPORT.md` — decision, results and readiness
- `reports/results.md` — detailed live metrics and interpretation
- `reports/paper_draft.md` — paper-format draft with real results
- `reports/experimental_protocol.md` — preserved prospective protocol
- `reports/HUMAN_DATASET_COLLECTION_BRIEF.md` — forwardable real-data collection and annotation specification
- `reports/SCREENSPOT_V2_VARIANTS_AUDIT.md` — official dataset audit and integration plan
- `reports/NEXT_STEPS_ACADEMIC_SUBMISSION_PLAN.md` — phased submission roadmap, roles, gates and schedule
- `data/academic_2000/` — reproducible 2,000-task candidate dataset, review queues, schema, checksums and source snapshots
- `reports/ACADEMIC_DATASET_2000_EXECUTION_PLAN.md` — exact annotation, freeze, execution, analysis and release procedure
- `reports/literature_review.md` and `reports/literature_matrix.csv` — source review
- `reports/novelty_assessment.md` — novelty gate
- `results/live_execution_summary.json` — machine-readable final summary
- `results/live_policy_metrics.csv` — policy table
- `results/live_stratified_metrics.csv` — category and family results
- `results/live_error_analysis.csv` — incorrect accepts and missed automation

The older `demo_*` files and non-prefixed plots are simulated software fixtures. Scientific conclusions use only `live_*` outputs.

## Limitations

The 200 labels are procedurally generated and have no independent human annotators. All layouts share one generator vocabulary, only two families are held out, and no licensed real-GUI cohort or independent grounding baseline was run. Zero errors among 26–30 accepted cases cannot support a low-risk guarantee. The current test set is spent and must not be used for further threshold tuning.
