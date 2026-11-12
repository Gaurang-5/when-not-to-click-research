# When Not to Click: Stress-Testing Native Jev 1.14 Visual Decisions on Absent and Ambiguous GUI Targets

**Draft status:** real synthetic pilot complete; external validation and human annotation remain required.

## Abstract

Visual grounding models may emit a location even when a requested GUI target is absent or non-unique. Jev 1.14 exposes a Noul presence judgment, a caller-defined none/one/several Choice and a Box with localization confidence. We evaluated whether frozen policies built from these native outputs improve click-or-abstain decisions beyond Box confidence. Our controlled pilot contains 200 synthetic GUI cases across five disjoint layout families and six target states. We fitted on 80 development cases, selected thresholds on 40 calibration cases and evaluated once on 80 held-out cases. Box confidence accepted 27/80 cases with ten incorrect clicks (37.0% selective risk), including 5/10 ambiguous targets. A frozen presence+uniqueness+Box gate accepted 26/80 with zero incorrect clicks, and a logistic gate accepted 29/80 with zero. A simpler uniqueness-only gate accepted all 30 eligible unique targets and no negative cases. The ambiguous-acceptance difference for the three-signal gate versus Box-only was −50 percentage points, but did not reach significance after the prespecified Holm correction (adjusted p=0.126). Total API cost was estimated at $0.0192. These results show useful native match-count discrimination on authored synthetic interfaces, while also showing that the joint gate did not outperform the simpler Choice gate. Procedural labels, shared generator conventions, two held-out families and the absence of an external baseline preclude deployment-safety or broad-generalization claims.

## 1. Introduction

GUI agents convert instructions into coordinates, but a coordinate alone is insufficient evidence that a requested target exists, is unique or is safe to click. TypeSafe's Box documentation notes that Box always returns a box and recommends accompanying presence and match-count questions. We test how much those native signals help under absent, duplicated, occluded, offscreen and unclear target states.

This work contributes an exact-interface measurement, not a new gating algorithm. It uses frozen source-selected policies, separates selective risk from marginal error and holds out complete layout families.

## 2. Related work and novelty boundary

SafeGround studies uncertainty calibration for GUI grounding; Argus studies uncertainty transfer; CORA calibrates execute/abstain decisions; OpenRef combines counting and localization; and several GUI benchmarks include negative or refusal behavior. Visual Jev, PixelJev and ImageJevBench create especially close overlap around Jev and selective grounding. These works rule out broad novelty claims for confidence gating, abstention or count-localization consistency. The residual contribution is the reproducible evaluation of Jev 1.14's exact native output trio on separately labelled negative states.

## 3. Dataset and task

The pilot contains 200 locally rendered screenshots: 25 templates nested in five layout families, with eight variants per template. Development uses sidebar and kanban families (80 cases), calibration uses tables (40), and test uses dialogs and toolbars (80). Each template contributes three unique cases and one each of absent, multiple, occluded, offscreen and unclear.

Ground truth comes from generator state and DOM geometry. A correct accepted click requires unique eligibility, predicted-center containment and IoU≥0.5. All clicks on non-eligible cases are incorrect. These procedural labels were not independently reviewed.

## 4. Model interface and policies

Each request pins `jev-1.14.0` and asks three questions over one screenshot: Noul presence, Choice with none/one/several criteria and Box localization. The parser rejects version drift, malformed probabilities and degenerate boxes.

Policy A accepts every valid Box. B thresholds Box confidence. C uses the minimum of presence and Box confidence. D uses the minimum of presence, one-match probability and Box confidence. E is an L2 logistic gate fitted on valid development outputs. Presence-only, uniqueness-only and presence+uniqueness gates are ablations. Calibration chooses the highest attainable coverage at or below 30%; all thresholds are frozen before test collection.

## 5. Metrics and analysis

Selective risk is incorrect accepted clicks divided by accepted clicks. Marginal incorrect-action rate divides by all attempted cases. We separately report coverage, absent false acceptance, multiple-target acceptance and correctly accepted unique targets divided by all eligible unique targets. Confidence intervals resample templates and paired tests use template-level sign randomization, with Holm correction across absent and multiple endpoints. Because only two families are held out, template intervals are descriptive rather than family-population inference.

## 6. Results

### 6.1 Operations and validity

The study issued 200 requests with no retries. All resolved to `jev-1.14.0`; 199 parsed successfully. One development offscreen case returned a zero-width Box and failed closed. Test collection produced 80/80 valid outputs. Total usage was 457,978 input and 15,425 output tokens, with estimated input cost of $0.019235. Test latency was 524 ms mean and 647 ms p95.

### 6.2 Held-out policies

| Policy | Coverage | Incorrect accepts | Selective risk | Multiple accepts | Useful unique automation |
|---|---:|---:|---:|---:|---:|
| Box threshold B | 33.8% | 10 | 37.0% | 5/10 | 56.7% |
| Presence + Box C | 27.5% | 5 | 22.7% | 5/10 | 56.7% |
| Three-signal D | 32.5% | 0 | 0% | 0/10 | 86.7% |
| Logistic E | 36.3% | 0 | 0% | 0/10 | 96.7% |
| Uniqueness-only | 37.5% | 0 | 0% | 0/10 | 100.0% |

All policies B–E rejected 10/10 absent cases. B's ten incorrect accepts were five multiple and five occluded targets. D made no incorrect accepts but missed four correctly localized toolbar targets; E missed one. The uniqueness-only gate accepted all 30 unique cases and no negative case.

All unique cases satisfied the primary localization rule; 27/30 reached IoU≥0.75 and mean IoU was 0.797. Thus errors in B were selection errors on ineligible cases rather than failed localization of eligible unique targets.

### 6.3 Primary comparison

Absent acceptance was zero for both B and D, producing no difference. Multiple-target acceptance fell from 50% under B to zero under D. The template-bootstrap difference interval was −0.80 to −0.20, while the small-sample cluster sign-randomization p-value was 0.063 before and 0.126 after Holm correction. We therefore report favorable direction and effect size without a significance claim.

The prospective practical criterion required at least ten-point reductions in both absent and multiple acceptance and no more than five-point loss in useful automation. It formally failed because Box-only already had zero absent acceptance. D improved multiple acceptance by 50 points and useful automation by 30 points.

### 6.4 Layout transfer

Box threshold B covered 62.5% of dialog cases but only 5% of toolbar cases. D covered 37.5% and 27.5%, respectively. E covered 35% in both. This suggests that semantic signals stabilized coverage within these two held-out families, but two families cannot establish general transfer.

### 6.5 Calibration

Held-out Brier/ECE were 0.152/0.191 for presence, 0.238/0.325 for Box confidence against correct localization, and 0.045/0.167 for the logistic score. These figures are descriptive because the sample is small and the component scores are dependent.

## 7. Error analysis

Box confidence failed to distinguish five duplicated and five occluded cases from eligible clicks. Presence removed the occluded errors but retained duplicated targets. Uniqueness removed duplicated targets and, in this generated cohort, also cleanly rejected every other negative state. The four D false rejections and one E false rejection were all toolbar unique targets with IoU between 0.778 and 0.803, indicating conservative semantic thresholds rather than localization failure.

One development output produced `left == right` at low Box confidence. The strict parser recorded it as a schema failure, retained its token usage and abstained. This validates fail-closed handling but also shows that HTTP 200 does not guarantee a usable localization.

## 8. Discussion

The primary empirical lesson is simpler than the original three-signal hypothesis: native match count carried nearly all useful discrimination on this authored pilot. The joint policies substantially improved over Box confidence but did not improve over uniqueness alone. A larger study should therefore treat uniqueness-only as a first-class baseline rather than assuming a joint gate is superior.

Zero observed errors among 26–30 accepts provide weak assurance. Under optimistic i.i.d. assumptions, 0/26 still gives a one-sided 95% upper error bound of about 10.9%; dependence and selection weaken that illustration further. The result supports further evaluation, not deployment certification.

## 9. Limitations

- Procedural labels have no independent human review.
- All interfaces share one synthetic generator and vocabulary.
- Only two layout families appear in the held-out split.
- There is no external real-GUI cohort or independent model baseline.
- Confidence outputs are dependent because they come from one shared request.
- Simulated candidate clicks do not measure downstream task harm.
- Results apply to one model version, prompt and date.

## 10. Ethics

The synthetic data contain no personal information. Credentials remain local environment variables; logs redact accidental key echoes. No real application actions were executed. Future public screenshots require license and privacy review.

## 11. Conclusion

Jev 1.14's native match-count signal cleanly separated unique from non-unique targets in this controlled synthetic pilot, while Box confidence alone accepted multiple and occluded targets. Frozen joint gates achieved zero observed incorrect accepts, but the simpler uniqueness-only gate achieved higher useful coverage. The effect did not reach adjusted significance in the small grouped primary test, and external validity remains untested. The justified next step is a human-reviewed, multi-application confirmatory cohort with uniqueness-only and independent grounding baselines.

## Reproducibility

Seed 1729; model `jev-1.14.0`; prompt `presence-count-box-v1`; primary IoU 0.5 plus center containment. The frozen policy and its digest are `results/live_frozen_policy.json` and `results/live_frozen_policy.sha256`. Live metrics, intervals, comparisons, calibration, errors and plots use the `live_*` prefix. The complete API log is append-only; raw responses are retained without credentials.
