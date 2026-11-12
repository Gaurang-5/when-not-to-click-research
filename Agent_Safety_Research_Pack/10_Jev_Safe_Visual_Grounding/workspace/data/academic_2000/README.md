# Jev Safe Visual Grounding Academic Candidate 2000

This directory contains a reproducible **2,000-task candidate manifest** for the next academic experiment. It is complete as a machine-readable construction package, but it is **not yet a publication-ready human-labelled benchmark**. The rows in `human_review_queue.csv` must be independently reviewed before claims are made from them.

## Composition

| Component | Primary tasks | Role |
|---|---:|---|
| ScreenSpot-v2-variants | 750 positive + 750 paired negative-instruction tasks | Real desktop, mobile and web GUI transfer cohort |
| ImageJevBench Box public v0.1 | 300 positive localization tasks | External box-localization and calibration cohort |
| Existing project synthetic pilot | 200 tasks | Controlled safety cases: unique, absent, multiple, occluded, offscreen and unclear |
| GUI-Recover CF Pilot | 66 auxiliary wrong-box candidates | Error analysis only; excluded from the 2,000 primary count |

The ScreenSpot selection contains at least one annotation from each of its 730 referenced images, plus 20 deterministic additional annotations. Every positive task is paired with a negative instruction on the same screenshot. Pairs share an `image_group_id` and proposed split to prevent image leakage.

## Files

- `manifest.jsonl` — canonical 2,000-row manifest; nested boxes remain native JSON.
- `manifest.csv` — spreadsheet-friendly mirror; nested values are compact JSON strings.
- `schema.json` — JSON Schema for a manifest row.
- `BUILD_REPORT.json` — counts and release state.
- `human_review_queue.csv` — 750 ScreenSpot absent-target candidates, 200 procedural synthetic cases, and any source geometry anomaly requiring two annotators and adjudication.
- `published_label_audit_sample_150.csv` — deterministic audit sample from the source-published positive labels.
- `counterfactual_candidates.csv` — 66 GUI-Recover wrong-click candidates linked to 15 samples. Do not score these as independent test cases.
- `sources.csv` — pinned source revisions and licensing notes.
- `source_snapshots/` — annotation/manifests used to reproduce this build; no third-party screenshots.
- `CHECKSUMS.sha256` — integrity hashes for the package.

## Label meanings

- `unique`: a source-published or procedurally generated visible target with one reference box.
- `absent_candidate`: the source supplies a negative instruction, but two humans must still confirm that no valid target is visible anywhere in the screenshot.
- `absent`, `multiple`, `occluded`, `offscreen`, `unclear`: controlled labels inherited from the local synthetic pilot; they remain subject to independent review.

An `absent_candidate` is never localization eligible and has no gold box. Do not silently convert it to confirmed `absent` until both annotators agree or adjudication resolves the case.

## Rebuild

From the project root:

```bash
.venv/bin/python scripts/build_academic_dataset.py
.venv/bin/python -m pytest -q
```

The build is deterministic against the pinned metadata snapshots.

## Materialize images for local experiments

External images are not redistributed in this package. Each row contains an immutable source URL and intended local path. Fetch and optionally resize them for Jev:

```bash
.venv/bin/python scripts/materialize_academic_images.py --source all --prepare-jev
```

This downloads 730 ScreenSpot images and 300 ImageJevBench images. ScreenSpot positive/negative pairs reuse the same file. `--prepare-jev` creates a maximum-1568-pixel copy while preserving aspect ratio; normalized gold boxes remain valid. ImageJev files are verified against their published SHA-256 values.

## Required human protocol

Use two annotators who work independently. For each row in `human_review_queue.csv`, each annotator chooses exactly one of `unique`, `absent`, `multiple`, `occluded`, `offscreen`, or `unclear`. For `unique` and `multiple`, they also draw every acceptable target box. A third person adjudicates every disagreement without seeing model predictions. Record changes in a new version; do not overwrite this candidate release.

After review:

1. Reject or rewrite negative instructions that name a visible or semantically valid control.
2. Replace source boxes that miss the clickable region.
3. Run the 150-row source-label audit. Expand to all source positives if the disagreement rate exceeds 5%.
4. Freeze grouped splits. No screenshot, application family, or paired instruction may cross splits.
5. Freeze the Jev prompt and all thresholds on development/calibration only.
6. Run the locked test and ImageJev external cohort once.
7. Report coverage, incorrect-accept rate, conditional accuracy, IoU, Acc@0.5, ECE/Brier score, latency, cost, and bootstrap confidence intervals.

## Licensing boundary

The package distributes metadata and local project assets only. ScreenSpot-v2 states Apache-2.0, but the variants repository does not publish its own clear licence metadata, so release review is required before redistributing variant screenshots. ImageJevBench has per-item licences and attribution; preserve them if images are redistributed. GUI-Recover annotations state CC-BY-4.0 while upstream screenshot terms continue to apply.
