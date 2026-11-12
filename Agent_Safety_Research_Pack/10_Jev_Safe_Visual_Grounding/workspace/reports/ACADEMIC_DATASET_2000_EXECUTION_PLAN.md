# Academic Dataset 2000: Execution Plan

## Current deliverable

The candidate dataset is assembled at `data/academic_2000/`. It has 2,000 primary tasks and 66 auxiliary GUI-Recover counterfactual boxes. The manifest is reproducible and structurally validated. It is not yet a human-labelled benchmark: 951 cases remain in the required review queue, and 150 source-published positives are in the audit sample.

## Why this composition is defensible

The real-GUI portion uses 730 distinct ScreenSpot-v2-variants screenshots across desktop, mobile and web. Each selected positive instruction has a paired negative instruction on the same image. The pair is kept in one image group, which prevents the same screenshot appearing in different splits.

ImageJevBench contributes all 300 public Box tasks as a locked external test cohort. It gives direct comparison with the published Box methodology, but it must not be used to tune the safety thresholds. Its 600 sealed examples are unavailable and are not represented as if they were downloaded.

The local 200-case cohort keeps the controlled safety phenomena absent from the public positive-localization sets. GUI-Recover contributes 66 plausible wrong-click boxes for error taxonomy and stress analysis, but its own authors describe the 15-screenshot release as a pilot, so those rows are auxiliary rather than benchmark observations.

## Phase 1 — materialize and inspect images

Run:

```bash
cd /Users/gaurangbhatia/Documents/Codex/2026-10-17/files-pasted-by-the-user-deep/outputs/jev_safe_gui_grounding
.venv/bin/python scripts/materialize_academic_images.py --source all --prepare-jev
```

Expected download: 1,030 unique external images (730 ScreenSpot plus 300 ImageJevBench). The 1,500 ScreenSpot tasks reuse 730 files. Preserve the original image and use `images/jev_ready/` for API input when a side exceeds 1,568 pixels. Check `materialized_images.csv`; ImageJev images are hash-verified automatically.

## Phase 2 — independent annotation

Give `human_review_queue.csv` and the materialized images to two annotators. Do not show them Jev predictions. Each annotator fills:

- `annotator_1_label` / `annotator_2_label` with one of `unique`, `absent`, `multiple`, `occluded`, `offscreen`, `unclear`;
- the corresponding `*_boxes_xyxy` as JSON such as `[[120,80,260,140]]` for unique or multiple targets;
- notes for borderline semantics;
- `review_status=complete` only after both entries are present.

Use a third adjudicator for every label disagreement or material box disagreement. The adjudicator fills the adjudicated label and boxes. One ScreenSpot positive is already queued because its published box extended one pixel beyond the stated image width; the candidate manifest clips that edge and preserves the original coordinates.

Separately complete `published_label_audit_sample_150.csv`. Enter `agree` when the source instruction and box are correct. If more than 5% disagree, audit all 1,049 remaining source-published positives before proceeding.

## Phase 3 — finalize and freeze

Run:

```bash
.venv/bin/python scripts/finalize_academic_labels.py
```

The command refuses to create a final manifest while a required review or audit is incomplete. It also rejects invalid label/box combinations. A successful run writes `manifest_reviewed.jsonl` and its SHA-256. Commit or archive that exact hash before any test call.

Freeze these items in the protocol:

1. Jev model version and question wording.
2. Resize policy and image hashes.
3. Development/calibration/test group assignments.
4. Safety gates and all thresholds.
5. Primary and secondary metrics.
6. Exclusion and transport-retry rules.

The 300 ImageJev cases remain `test_external`. Do not use them for threshold selection.

## Phase 4 — preflight before spending credits

Run 20 development cases covering positive, absent, multiple, occluded, offscreen and unclear labels. Verify response parsing, coordinate conversion, append-only logging, retry behavior, and absence of API keys from logs. Then run 50 calibration cases and estimate cost from the returned token usage:

```bash
.venv/bin/python scripts/estimate_cost.py --log results/academic_preflight_calls.jsonl
```

The completed 200-call pilot cost about $0.019235, so a simple same-usage extrapolation is about $0.192 for 2,000 calls. Treat that only as a planning estimate because image sizes and service pricing can differ. Budget extra for transport failures and any separately registered baseline models.

## Phase 5 — locked execution

Run in this order:

1. Development cases for parser and protocol debugging only.
2. Calibration cases to choose the frozen click/abstain threshold.
3. Main held-out test exactly once.
4. ImageJev external test exactly once.
5. Baseline model on the same prepared images and prompt contract.

Never tune a threshold after seeing test outcomes. Append every attempt to an immutable JSONL log, including failures. Do not count an API transport error as an absent-target prediction.

## Phase 6 — analysis for the paper

Primary safety table:

- coverage (fraction of tasks on which the policy clicks);
- incorrect-accept rate over all tasks;
- conditional accuracy among accepted clicks;
- recall of safe unique targets;
- rejection rates for absent, multiple, occluded, offscreen and unclear cases.

Localization/calibration table:

- mean IoU, Acc@0.5 and Acc@0.75 on eligible unique targets;
- ECE and Brier score for the event IoU ≥ 0.5;
- risk-coverage curves and selective risk at frozen operating points;
- latency p50/p95 and measured API cost.

Report 95% screenshot-group bootstrap intervals. Compare policies on paired cases with paired tests. Give results by platform, source, element type, target size and layout family. The main claim should concern whether a frozen safety policy transfers from controlled development data to real desktop/mobile/web interfaces; do not claim general GUI safety from this public-data study.

## Phase 7 — release package

Release metadata, scripts, checksums, finalized annotations, evaluation code, and result logs. Redistribute images only after licence review. If image redistribution remains unclear, publish source URLs, hashes, and the materializer instead. Preserve ImageJev’s per-item attribution and ShareAlike terms where applicable.

The paper should label the 2,000-row file as a benchmark only after Phase 2 and Phase 3 finish. Until then call it the “candidate evaluation corpus.”
