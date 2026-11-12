# Iteration 3: reviewer-driven research expansion

Authorized: implement analyses, new same-data model baseline, repeated Jev calls and prompt sensitivity. Never fabricate human labels or a new untouched holdout.

1. Freeze an exploratory design before new collection: deterministic source-cluster 40/30/30 split of 751 real cases; no claim that previously inspected outcomes become confirmatory.
2. Offline: A/B/final/consensus-only label sensitivity; center, IoU0.3 and strict criteria; directional human-box agreement; Brier skill relative to retrospective and calibration-only constants; AUROC/AURC with source-cluster intervals.
3. Recalibration: threshold-only empirical operating points and Learn-then-Test with finite fixed threshold grid, exact one-sided binomial tests and Bonferroni correction. Use one independently selected case per source cluster for calibration/testing guarantee target; report full-case metrics descriptively. A real-trained logistic diagnostic uses fit partition only. No forced result when no threshold passes.
4. Baseline: Qwen2.5-VL-7B via Ollama, quantization and model digest recorded; one serial request, deterministic decode, all951 same inputs. Fix JSON prompt/schema before model results, output box and verbal presence/uniqueness scores. These are prompted scores, not native-calibrated Jev probabilities.
5. Jev repetitions: five total passes on751 real cases (existing pass plus four new); original prompt and two prewritten variants; resumable, no silent retries; environment key required. Separate request identities per case/repeat/prompt; freeze and hash manifests. Report failure/consistency and between-repeat metric variation.
6. New balanced real cohort: prepare disjoint source-image candidates from unused source data and a blinded human annotation package. Do not label auto-generated status as human truth; no fresh confirmatory results without labels.
7. Integrate only completed evidence into paper; retain unavailable/human-pending work explicitly. Compile/render/inspect, tests, checksums, update status.

Local inference is serial to limit memory pressure. No unstated cloud hardware cost is assumed.
