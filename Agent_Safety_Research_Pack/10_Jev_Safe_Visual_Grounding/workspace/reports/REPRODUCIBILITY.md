# Offline reproduction

The workflow uses saved API outputs. It does not request an API key or make paid calls.

## Existing workspace

Run from workspace/:

```sh
JEV_DOCUMENT_PYTHON=/Users/gaurangbhatia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/reproduce_offline.sh
```

The analysis environment is .venv. A portable setup uses requirements.txt for analysis and requirements-documents.txt for PDF building in the same or a separate Python environment. Set JEV_ANALYSIS_PYTHON and JEV_DOCUMENT_PYTHON to override interpreter paths.

## Restricted inputs

The code-only package requires the retained data and results from this research workspace:
- results/live_calls.jsonl and live_frozen_policy.json plus its sha256 sidecar;
- results/external_confirmatory_calls.jsonl;
- data/pilot_cases.jsonl;
- data/academic_2000/manifest.jsonl;
- annotation_round_1 frozen_labels, corrected_analysis/case_comparison.csv, external_confirmatory/cases.jsonl and images;
- original source screenshot files referenced in source_image.

These inputs must match the archived source revisions and checksums. Raw images and human exports are not redistributed in the code-only ZIP pending privacy and licensing review. A repository URL and data-access process must be added by the authors before public release. Do not substitute standard ScreenSpot-v2 scores for this counterfactual cohort.

## Outputs

results/extended/ contains source decomposition, confidence intervals, stratified_metrics.csv, risk-coverage sweeps, reliability bins, cost assumptions, utility sensitivity and the synthetic overlap hash audit. paper/main.tex and output/pdf/jev_safe_visual_grounding_paper.pdf are generated from scripts/paper_content.py, so their claims stay synchronized.

The LaTeX project includes local figures and can compile independently. The standalone source mirror under workspace/reports is a reference copy; compile paper/main.tex.

## Pending human evidence

reviewer_audit contains a blinded 100-case queue. Give only blind_review.csv, images/, and REVIEWER_INSTRUCTIONS.md to a human reviewer; do not share RESEARCHER_ONLY_mapping.csv. No independent adjudication has yet been performed. New labels must create a versioned sensitivity dataset rather than silently changing the frozen study.

## Reviewer expansion

The saved-data reproduction also runs reviewer_analysis.py and evaluate_iteration3_collection.py. The former needs corrected_exports/annotator_a_corrected.json and annotator_b_corrected.json; the latter reads the completed new logs under results/iteration3/. Protocols and the real source-cluster split are under reports/iteration3/. No paid collectors are invoked by reproduce_offline.sh.

New collection is separate: run_iteration3_jev.py --execute-live (environment API key, 4,506 planned new requests), or run_local_baseline.py --execute-local (Ollama, pinned downloaded model). Both are serial and resumable; attempted malformed/timeout outputs remain failures. A dry run omits the execute flag. Do not run a second collector while one is active.

## Complete same-input comparison inputs

The expanded reproduction requires results/iteration3/jev_repeated_calls.jsonl and its .sha256, qwen_baseline_calls.jsonl and its .sha256, reports/iteration3/baseline_protocol.json, the retained Jev collection protocol/hash, and the fixed real_cluster_split.json. These contain restricted experiment inputs and are supplied separately from the code-only ZIP. The render_iteration3_comparison.py step refuses partial model collections. Evaluator validation checks all951 input IDs, pinned Qwen protocol/model identity and image-hash equality against Jev; each complete raw log is checked against its frozen sidecar.

Primary same-data geometry is real-only (751 cases;131 unique under final labels). The shared semantic one-label rule is independent of Jev-trained logistic policy E; no E coefficients are transferred to Qwen. Alternative-label tables change the human reference while preserving predictions. Timing compares complete951-input deployments, with no matched-hardware claim. Local energy/hardware are unpriced.

## Journal manuscript typography

The PDF/TeX builder applies scripts/paper_layout.py to the same scientific content. Include that module when reproducing the manuscript. The generated TeX project includes jev_journal.sty alongside main.tex and figures/. Formatting details and integrity checks are in PAPER_FORMAT.md.
