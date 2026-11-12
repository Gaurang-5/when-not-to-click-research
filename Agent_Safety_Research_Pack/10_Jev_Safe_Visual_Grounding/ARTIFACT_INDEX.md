# JEV audited research artifact

## Manuscript

- output/pdf/jev_safe_visual_grounding_paper.pdf: updated audited paper with mathematical analysis, published VLM context and diagnostic appendices.
- paper/main.tex: editable, standalone LaTeX project; figures are in paper/figures/extended/.
- workspace/scripts/paper_content.py: shared text/tables for TeX and PDF.
- archive/2026-10-23-preaudit/: superseded manuscript, retained for transparency. Do not use its strong transfer conclusion.

## Evidence

- workspace/results/extended/summary.json: real-only and mixed results, cluster intervals, calibration, cost assumptions and overlap audit.
- workspace/results/extended/cohort_metrics.csv: all source-cohort policy metrics.
- workspace/results/extended/stratified_metrics.csv: platform, status, size, confidence, provenance, source, element and instruction-length diagnostics.
- workspace/results/extended/case_ledger.csv: per-case acceptance/correctness ledger.
- workspace/results/extended/synthetic_overlap_audit.csv:200 exact pilot repeats, including120 fitting/calibration cases.
- workspace/results/external_confirmatory_calls.jsonl: immutable raw collection records.
- workspace/results/external_confirmatory/summary.json: legacy mixed-cohort evaluation with corrected usage accounting; interpret together with real-only diagnostics.
- workspace/reports/AUDIT_CORRECTIONS.md: changes in interpretation and accounting.
- workspace/reports/published_comparison_sources.json: provenance of published VLM values and official prices.

## Reproduction and pending human review

- workspace/scripts/reproduce_offline.sh: saved-data-only reproduction, no paid calls.
- workspace/reports/REPRODUCIBILITY.md: environment, inputs and restricted-data access notes.
- workspace/reviewer_audit/:100 blinded cases prepared, not reviewed. Keep RESEARCHER_ONLY_mapping.csv with authors.
- workspace/reports/RESEARCH_COMPLETION_STATUS.md: complete execution versus pending evidence and submission tasks.
- CODE_ONLY_REPRODUCIBILITY.zip: shareable code/docs package without raw screenshots, labels or credentials. Dataset access remains restricted.

## Reviewer expansion, 23 October 2026

- workspace/results/iteration3/reviewer_analysis_summary.json and CSVs: executed sensitivity, Brier/ranking, human geometry and exploratory recovery analyses.
- workspace/results/iteration3/collection_summary.json: refreshable repeat/prompt and local-baseline collection snapshot. Partial cohorts are marked.
- workspace/reports/iteration3/: frozen protocols, exact source-cluster split, implementation plan and reviewer-response ledger.
- FRESH_REAL_180_BLINDED_ANNOTATION.zip: private two-annotator handoff, 180 candidate tasks /60 images; no labels or model predictions. Researcher source mapping excluded.
- workspace/fresh_real_review/RESEARCHER_ONLY_manifest.json: author-only construction mapping, never give to annotators.

## Completed same-data baseline

- workspace/results/iteration3/qwen_baseline_calls.jsonl and .sha256:951 raw records, frozen model/prompt and951 matched input-image hashes.
- workspace/results/iteration3/same_data_model_case_ledger.csv:real-only per-case geometry under both models.
- workspace/results/iteration3/same_data_label_sensitivity.csv:alternative human references and localization criteria.
- workspace/results/iteration3/same_data_comparison.png:completed geometry comparison with paired source-cluster intervals.
- workspace/results/iteration3/collection_summary.json:all planned collection state COMPLETE; human annotation/audit is tracked separately.

## Paper formatting, 1 November 2026

The PDF and paper/main.tex follow the professor-supplied journal article: blue sans-serif headings, a shaded abstract, serif body and author-year citations. paper/jev_journal.sty defines the editable LaTeX style. workspace/reports/PAPER_FORMAT.md records the measured layout and verification. The prior conference version is archived in archive/2026-11-01-before-professor-format/. Numerical evidence is unchanged.

workspace/reports/WRITING_SKILLS.md records the two globally installed writing/cleanup skills and the user-wide writing instruction.
