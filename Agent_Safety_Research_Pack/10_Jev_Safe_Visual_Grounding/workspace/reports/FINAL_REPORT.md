# Final research and execution report

## Executive decision

**CONDITIONAL GO** for expanding the study to human-reviewed, real-interface data. **NO-GO** for claiming that a three-signal gate is a novel method or that this pilot establishes deployment safety.

The real Jev 1.14 pilot is complete. On 80 held-out synthetic cases, Box-confidence policy B accepted 27 cases with 10 incorrect clicks. Frozen three-signal policy D accepted 26 with zero incorrect clicks, and logistic policy E accepted 29 with zero. The simplest uniqueness-only gate performed best: 30 correct accepts and zero incorrect accepts. The primary ambiguous-target effect favored D by 50 percentage points but was not significant after the prespecified Holm correction (adjusted p=0.126). Both B and D rejected all absent cases.

## Research question and novelty

The study asks whether native Jev presence, match-count and localization scores improve click-or-abstain decisions beyond Box confidence under held-out layout families. The literature review shows that semantic presence/count gating, selective prediction and frozen threshold transfer are prior art. TypeSafe's own Box documentation recommends Noul presence and none/one/several Choice checks. The defensible contribution is measurement of this exact interface, with explicit negative states and a reproducible frozen evaluation.

Closest work includes SafeGround, Argus, CORA, OpenRef, Visual Jev, PixelJev and ImageJevBench. Full evidence and overlap ratings appear in `literature_review.md`, `literature_matrix.csv`, `jev_competitors.md` and `novelty_assessment.md`.

## Dataset and design

The controlled pilot contains 200 screenshots, 25 templates and five non-overlapping layout families: 80 development, 40 calibration and 80 test cases. It separates unique, absent, multiple, occluded, offscreen and unclear states. Primary localization requires unique eligibility, predicted-center containment and IoU≥0.5. Policies were calibrated to the highest attainable source coverage at or below 30%; test thresholds were never retuned.

The labels are DOM-derived and procedural. Independent human annotators: zero. Public ScreenSpot schemas were audited, but public images were excluded because existing annotations do not establish absent or ambiguous status.

## Live execution

- API requests: 200, with no retries.
- Valid parsed outputs: 199.
- Schema failures: one development offscreen case with a zero-width Box; retained and failed closed.
- Held-out test outputs: 80/80 valid.
- Resolved model: `jev-1.14.0` for all 200 responses.
- Usage: 457,978 input and 15,425 output tokens.
- Estimated total cost: **$0.019235**.
- Test latency: 524 ms mean, 521 ms median, 647 ms p95.
- Verification: **55 tests passed**.

## Held-out findings

| Policy | Coverage | Incorrect accepts | Selective risk | Ambiguous accepts | Useful unique automation |
|---|---:|---:|---:|---:|---:|
| B: Box confidence | 33.8% | 10 | 37.0% | 5/10 | 56.7% |
| C: presence + Box | 27.5% | 5 | 22.7% | 5/10 | 56.7% |
| D: presence + uniqueness + Box | 32.5% | 0 | 0% | 0/10 | 86.7% |
| E: logistic joint gate | 36.3% | 0 | 0% | 0/10 | 96.7% |
| Uniqueness-only | 37.5% | 0 | 0% | 0/10 | 100.0% |

The result supports using the native Choice count signal on this dataset. It does not support the stronger claim that combining all three signals is necessary: uniqueness alone dominated the combined policies here. It also exposes Box-confidence transfer instability: B covered 62.5% of dialogs and 5% of toolbars. E reached 35% coverage in each held-out family.

The prospective practical criterion formally failed because B already had zero absent false accepts, leaving no possible ten-point reduction for D. D nevertheless reduced ambiguous acceptance from 50% to zero and increased useful unique automation by 30 points. The paired ambiguous comparison remained underpowered after multiplicity correction.

## Limitations and claim boundary

The observed zero-error policies have only 26–30 accepted cases. Under an optimistic i.i.d. calculation, zero errors among 26 accepts still permits a one-sided 95% upper bound of about 10.9%. The screenshots are dependent, so this is not a valid deployment guarantee. Two held-out families are inadequate for population-level family inference.

Synthetic interfaces share generator conventions; procedural labels lack independent review; no real downstream clicks were executed; and no external model baseline or licensed real-GUI cohort was evaluated. Results apply only to this model version, prompt, synthetic distribution and freeze.

## Submission readiness

| Dimension | Rating | Reason |
|---|---:|---|
| Novelty | 4/10 | Exact-interface measurement gap; method overlaps prior art |
| Methodological rigor | 7/10 | Prospective splits, frozen hash and explicit denominators; small clustered pilot |
| Reproducibility | 9/10 | Version, prompts, logs, hashes, dataset, code, tables and 55 tests |
| Experimental completeness | 6/10 | Real Jev pilot complete; human review, external cohort and baseline missing |
| Potential research value | 7/10 | Clear signal and useful negative result about gate complexity |

Current status: **pilot complete, not submission-ready**. The next scientific step is an independently annotated external cohort with many more application families, followed by a new frozen confirmatory test and a comparable baseline. The current test set must not be reused for further threshold selection.
