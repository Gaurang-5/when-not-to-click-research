# Experimental protocol — 17 October 2026

Status: executed Jev pilot. This file preserves the prospective protocol written before final-test collection; it was a local protocol, not a public preregistration. Development and calibration outputs were collected, thresholds were frozen and hashed, and the held-out test was then collected once. Any further tuning requires a new untouched confirmatory cohort.

## Question and scope

**Do native Jev 1.14 presence, match-count and localization scores add useful rejection information beyond Box confidence on absent and ambiguous GUI targets, and how does the frozen decision policy behave on held-out layout families?**

RQ1 presence discrimination; RQ2 unique-versus-multiple discrimination; RQ3 added value of combined scores; RQ4 transfer to held-out layouts; RQ5 risk, coverage and operational cost. Hypotheses are directional candidates, not assumed results. No new risk-control algorithm or universal safety guarantee is claimed.

## Unit and ground truth

D={(I,q,y,B,M,A)}. A case contains screenshot, instruction, status, all plausible boxes, match count and reference action. The independent sampling unit is an application/layout family; screenshot variants within a family are dependent. Generated templates are nested inside five layout families, and all screenshots of a family belong to one split. Different colors or IDs alone do not constitute independent templates. Shared generator conventions remain an external-validity limitation.

Six mutually exclusive primary statuses: unique, absent, multiple, occluded, offscreen, unclear. Preserve separate visibility, count and eligibility fields where mixed states exist. Unique means exactly one visible, actionable, sufficiently legible target. Absent means no corresponding element in the constructed application state. Offscreen means an element exists in application state but not the current image. These two states can be observationally indistinguishable to an image-only model: do not score their differentiation as a required model capability. Occluded targets require uncovering; multiple targets require clarification; unclear targets require zoom or better evidence. Conservative reference decisions do not imply every partly occluded real target is unclickable.

Primary localization criterion: eligible unique target, predicted center inside its visible hit region AND IoU >=0.5 against the reference box. IoU >=0.75 is secondary; center-only accuracy is an additional click-relevant sensitivity analysis. A prediction failing the criterion is not a correct accepted click. A huge box enclosing the target cannot earn success just by overlap. All clicks on non-eligible cases count as incorrect under this controlled protocol. Actual application effects are not executed.

## Data and annotation

Pilot: 200 synthetic HTML screenshots, 25 templates ×8 cases, nested in five layout families. Each template: three unique, one absent, one multiple, one occluded, one offscreen, one unclear. Development 80 cases/two families; calibration 40/one family; final test 80/two families. Test: 30 unique and 10 of each other category. This intentionally includes close contrasts within splits. It is a pipeline pilot, not a representative prevalence sample.

DOM-derived geometry and known generated state are procedural ground truth, not human agreement. Annotator fields remain null until real review. Before model evaluation, two independent annotators should view each screenshot and instruction without model outputs or the other's labels, mark visible plausible candidates and safe reference action, then adjudicate discrepancies using a third reviewer. Report raw categorical agreement and Cohen's kappa on status; report count agreement and matched-box IoU separately. Undefined kappa (one observed category) stays undefined. Preserve original labels, adjudication reason and versions. Exclude a case only for preregistered corrupt image, invalid geometry or unresolved label ambiguity; never exclude a model failure. Report every exclusion by split/status.

Public screenshots are a distinct external cohort. A ScreenSpot license/schema audit is supplied; no public images are silently counted in the 200 cases. Existing positive-target annotations do not establish absence or uniqueness. Reannotation and source-specific grouping must precede their use. Freeze source revisions and hashes, respect attribution and inspect for identifying information. Avoid duplicates and near-identical screens across splits.

## Policies and fair comparison

A accepts every syntactically valid Box. Errors and missing boxes abstain and remain in coverage denominator.
B thresholds Box confidence.
C requires presence and Box confidence.
D requires presence, exactly-one probability and Box confidence.
E fits a regularized logistic gate on development cases only to predict correct actionable localization, with native scores as features; selects its threshold on calibration only. This is an existing-method baseline, not a new algorithm.

Evaluate presence-only, uniqueness-only, presence+uniqueness and Box-only ablations with the same available Box as click candidate. Do not multiply scores and call their product a joint probability; outputs may be strongly dependent. Compare raw and optionally sigmoid-calibrated presence probabilities only when both classes and enough development observations exist. Temperature scaling is not appropriate without an explicit compatible logit representation.

The demonstration can use a simple one-parameter min-score gate for C/D and must label that simplification. The real study should additionally tune separate component thresholds on development, then freeze these combinations and choose one calibration operating point; it must not search unrestricted threshold combinations on 40 calibration examples and call the result certified.

Primary policy comparison: D versus B, with separate absent false-accept and ambiguous acceptance endpoints; Holm correction across these two tests. Set operating thresholds using source calibration to target total coverage <=30%, choosing the highest attainable coverage (ties: more conservative threshold). Report realized test coverage and correctly accepted unique-target coverage beside every comparison. This is matched *source* coverage, not guaranteed matched target coverage. A cannot be forced to 30% without changing its definition. C/E and other operating points are secondary. Curves on test are descriptive sweeps, never deployed threshold selection. Any post-hoc matched-test-coverage comparison is explicitly exploratory.

Prospective practical criterion: at least 10 percentage points reduction in each negative-category acceptance rate with no more than 5 percentage points loss of useful unique-target acceptance versus B. This is a provisional engineering tolerance, **not pilot-derived or powered** because no Jev pilot exists. Pilot variance and discordant-pair counts must inform the subsequent confirmatory sample-size calculation before new test collection. Failure to meet significance in this pilot does not establish equivalence.

## Metrics: explicit denominators

- Absent false accept: accepted absent / all absent cases, including failed calls.
- Ambiguous acceptance: accepted multiple / all multiple cases. No unique intended referent exists, so this measures unauthorized disambiguation rather than guessing which duplicate the user secretly intended.
- Selective risk: incorrect accepted / all accepted. Undefined when no clicks accepted, not zero.
- Marginal incorrect-action rate: incorrect accepted / all attempted cases. This differs from selective risk and is reported separately.
- Coverage: accepted / attempted. Clarification and abstention: corresponding action / attempted.
- Useful automation: correct accepted / all eligible unique cases, and separately / all attempted cases.
- IoU and Acc@0.5/.75: eligible unique cases; failed or missing localization counts as zero for unconditional accuracy; valid-output-only metrics are explicitly secondary.
- Presence Brier: mean squared probability error, with truth meaning visibly identifiable presence (unique, multiple, occluded as specified in annotation; offscreen and absent negative; unclear requires fixed definition). Report missing-score counts; do not impute absent API outputs as probabilities. Report the exact implementation convention.
- ECE: ten fixed equal-width bins [0,.1),…,[.9,1], weighted absolute gap between mean score and event frequency; reliability plots include counts. Small category cells are descriptive. Box confidence is evaluated against a separately defined localization-success event, not treated as presence probability.
- Risk–coverage: descending score ranking, tied scores accepted together; AURC interpolation and attainable range documented, no extrapolation beyond valid coverage. All-zero acceptance has undefined selective risk.
- Operations: request count, primitive count, attempt count, error type, retry fraction, wall-clock latency and billed token usage. Three questions in one request are not three network calls. Shared combined requests permit paired offline policy comparisons but cannot establish standalone policy latency/cost. Separate randomized standalone calls are required for operational comparisons.

Report by status, template, layout family, target size and difficulty/clutter where annotations support them. Unique-small and unclear are different labels; do not confuse them.

## Statistical analysis and risk claims

Bootstrap complete clusters, keeping paired policy outcomes and all screenshot variants together. Template-cluster intervals are descriptive if templates share a family; two test families are inadequate for robust family-level inference. Report leave-one-family-out sensitivity and family-specific point estimates rather than claiming narrow population confidence. For a larger confirmatory cohort, increase independently authored applications/families before adding more near-duplicates.

Paired differences use cluster bootstrap and, with sufficient clusters, a cluster-level sign-flip/permutation analysis. Ordinary screenshot-level McNemar assumes independent pairs and is unsuitable as the primary clustered test. Holm adjusts the two primary category hypotheses. Secondary tests are exploratory. No equivalence claim without a prespecified equivalence margin and suitable power.

For fixed-policy independent Bernoulli trials with zero errors, the one-sided 95% exact upper bound is 1-0.05^(1/n). At least 299 accepted independent decisions are needed to put this below 1%; n=200 gives about 1.49%, and n=10 gives about 25.9%. These are optimistic illustrations, not bounds valid for dependent screenshots, selected thresholds or shifted deployment. Calibration threshold search needs simultaneous correction or a separate validation set. With 20 prespecified candidates and Bonferroni correction, zero-error sample requirement becomes ceil(log(.05/20)/log(.99))=597 accepted independent cases. Larger screenshot counts cannot substitute for independent families.

A Learn-then-Test style bound requires frozen candidate policies and suitable exchangeable/independent calibration units. The present coverage-calibrated demo does not implement a certified risk controller. Distribution shift breaks naive transfer guarantees. Analyze empirical degradation on unseen families; do not relabel source calibration as certified target-domain risk control. CORA's equation for harm × execution controls a marginal rate, which should not be mistaken for conditional risk among executed actions. See [CORA §3.4](https://arxiv.org/html/2604.09155) and [Learn then Test §1–3](https://arxiv.org/html/2110.01052v5).

## Execution and freeze

1. Validate files, dimensions, labels, groups and hashes; resolve human disagreements.
2. Smoke-test one known positive and negative development case using pinned jev-1.14.0; validate polarity, version and full response schema. Never silently substitute jev-preview.
3. Collect development and calibration responses; keep final-test output inaccessible to tuning. Fit gates, freeze all settings and hash manifest.
4. Collect final-test responses once. Missing outputs fail closed; all attempts remain in denominators. Retry only transient documented errors, cap retries and log attempts; schema/version errors require protocol review, not silent coercion.
5. Analyze frozen policies, publish raw redacted response logs and per-family results. Report test reuse if prompts were revised.

## Scientific interpretation

A negative result is valuable if checks add cost without useful discrimination, if source-selected coverage collapses, or if a simple Box gate matches the joint gate. A positive synthetic result alone establishes neither arbitrary-interface generalization nor prevention of downstream harm. The study concerns image-grounded candidate decisions, not full task execution safety.
