# Live Jev 1.14 results

## Execution ledger

The experiment made 200 API requests on 17 October 2026: 80 development, 40 calibration and 80 held-out test cases. Every response resolved to `jev-1.14.0`; 199 parsed successfully. One development offscreen case returned HTTP 200 with a zero-width Box and was retained as a fail-closed schema error. No request was retried. The final test produced 80/80 valid outputs.

Total usage was 457,978 input tokens and 15,425 output tokens. At $0.042 per million input tokens, estimated total cost was **$0.019235**. The test split cost estimate was **$0.007695**. Test latency was 524 ms mean, 521 ms median and 647 ms p95. Cost is calculated from returned usage and is not an invoice.

Thresholds and logistic coefficients were frozen after development and calibration. The SHA-256-protected freeze states that test data were not used for selection. The held-out test was evaluated once.

## Frozen held-out results

| Policy | Accepted | Coverage | Selective risk | Marginal incorrect action | Absent false accept | Ambiguous wrong accept | Useful unique automation |
|---|---:|---:|---:|---:|---:|---:|---:|
| A: every valid Box | 80/80 | 100.0% | 62.5% | 62.5% | 100% | 100% | 100.0% |
| B: Box confidence | 27/80 | 33.8% | 37.0% | 12.5% | 0% | 50% | 56.7% |
| C: presence + Box | 22/80 | 27.5% | 22.7% | 6.3% | 0% | 50% | 56.7% |
| D: presence + uniqueness + Box | 26/80 | 32.5% | **0%** | **0%** | 0% | **0%** | 86.7% |
| E: logistic joint gate | 29/80 | 36.3% | **0%** | **0%** | 0% | **0%** | 96.7% |
| Uniqueness-only Choice gate | 30/80 | 37.5% | **0%** | **0%** | 0% | **0%** | **100.0%** |

Selective risk is incorrect accepted clicks divided by accepted clicks. Useful unique automation is correctly accepted unique cases divided by all 30 eligible unique cases. Policy B's ten incorrect accepts comprised five multiple-target and five occluded-target cases. D and E made no incorrect accepts; D abstained from four correctly localized toolbar targets and E from one. The uniqueness-only gate accepted all 30 correctly localized unique cases and no negative case, making it the strongest simple policy in this controlled pilot.

All 30 unique targets were localized with center containment and IoU≥0.5 before gating; 27/30 reached IoU≥0.75. Mean unique-target IoU was 0.797.

## Primary comparison and prospective criterion

For absent cases, both B and D accepted 0/10, so D−B was 0.00 (template-bootstrap interval 0.00 to 0.00; Holm-adjusted cluster sign-randomization p=1.0). For multiple-target cases, B accepted 5/10 and D accepted 0/10: D−B was −0.50 (descriptive template-bootstrap 95% interval −0.80 to −0.20; unadjusted p=0.063; Holm-adjusted p=0.126). The direction is favorable, but the small grouped test does not meet the adjusted significance threshold.

The literal prospective engineering criterion was not met because it required at least a ten-point improvement on both negative categories. B was already perfect on absent cases, so the absent improvement was zero. D improved ambiguous acceptance by 50 points and useful unique automation by 30 points. This is reported as a criterion failure; the criterion was not changed after seeing test results.

Zero observed errors do not establish zero deployment risk. Even under optimistic independent Bernoulli assumptions, 0/26 accepted errors gives a one-sided 95% upper bound of 10.9% for D; 0/29 gives 9.8% for E. Screenshot dependence and threshold selection make those illustrations optimistic.

## Transfer and calibration

Box-only B showed severe family sensitivity: 62.5% coverage on dialogs versus 5.0% on toolbars. Its selective risk was 40% on dialogs. D covered 37.5% of dialogs and 27.5% of toolbars with zero observed accepted errors. E covered 35% in each family with zero observed accepted errors. This is useful transfer evidence within the authored generator, but two held-out families cannot characterize family-level uncertainty.

Held-out Brier/ECE values were 0.152/0.191 for presence, 0.238/0.325 for Box confidence against correct localization, and 0.045/0.167 for the development-fitted logistic score. These are descriptive because the pilot is small and scores are dependent.

## Interpretation

The synthetic pilot supports a narrow conclusion: Jev 1.14's native `none/one/several` Choice output separated the authored unique and non-unique cases much better than Box confidence. Presence helped remove occluded cases when combined with Box confidence, while uniqueness removed ambiguity. The joint gates were safe on the observed test but did not beat the simpler uniqueness-only gate.

This result does not establish performance on real applications, safety under distribution shift or prevention of downstream harm. Labels are procedural and unreviewed, all interfaces share one generator vocabulary, there are only two held-out families, and no independent grounding baseline or external GUI cohort was run.

## Live artifacts

- `results/live_policy_metrics.csv`
- `results/live_stratified_metrics.csv`
- `results/live_confidence_intervals.csv`
- `results/live_comparisons.json`
- `results/live_calibration.json`
- `results/live_error_analysis.csv`
- `results/live_execution_summary.json`
- `results/live_risk_coverage.png`
- `results/live_reliability.png`
- `results/live_policy_comparison.png`
- `results/live_localization.png`

The older `demo_*` files remain only as provenance-labelled software fixtures and are not used in these conclusions.
