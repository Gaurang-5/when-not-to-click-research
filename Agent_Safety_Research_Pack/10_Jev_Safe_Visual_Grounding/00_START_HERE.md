# Jev safe visual grounding study

This folder is the canonical home of the active Jev experiment. The complete runnable project is preserved intact in [`workspace/`](workspace/). The numbered links provide shorter entry points without duplicating files.

## Current status - 1 November 2026

Read [the verified execution status](workspace/reports/RESEARCH_COMPLETION_STATUS.md) and [reviewer-response ledger](workspace/reports/iteration3/REVIEWER_RESPONSE.md). Original pilot and human-reviewed evaluation are complete; the source audit separates 751 real cases from 200 reused pilot cases. Reviewer-requested offline analyses are executed and in the paper. Both the Jev repeat/prompt study and the 951-input local Qwen baseline are complete. Human review of fresh tasks and the independent audit remain pending.

The current [PDF](output/pdf/jev_safe_visual_grounding_paper.pdf) and [LaTeX source](paper/main.tex) use the professor-requested journal manuscript layout and distinguish completed evidence from pending experiments. [Formatting notes](workspace/reports/PAPER_FORMAT.md) document the sample, editable style and integrity checks. The candidate 2,000-task manifest is not a 2,000-case human-validated benchmark.

## Read in this order

1. [Current manuscript](output/pdf/jev_safe_visual_grounding_paper.pdf): completed experimental results and stated limitations.
2. [Execution status](workspace/reports/RESEARCH_COMPLETION_STATUS.md): completed automated work versus pending human work.
3. [Reviewer-response ledger](workspace/reports/iteration3/REVIEWER_RESPONSE.md): each requested improvement and its evidence.
4. [Offline reproduction](workspace/reports/REPRODUCIBILITY.md): commands, required restricted inputs and outputs.
5. [Fresh annotation instructions](workspace/fresh_real_review/README_FIRST.md): the additional 180-task cohort, separate from the completed 951-case study.

Older pilot reports and candidate-dataset plans remain historical records; the files above are the current entry points.

## Folder map

| Entry | Purpose |
|---|---|
| `01_Manuscript_and_Reports` | Link to reports, literature review, protocol, manuscript draft, and plans |
| `02_Dataset_2000` | Link to the candidate manifest, source audit, checksums, and human review queue |
| `03_Human_Annotation` | Link to Label Studio configuration, instructions, and blinded task bundles |
| `04_Experiment_Results` | Link to live outputs, metrics, confidence intervals, plots, and frozen policy |
| `05_Execution_Scripts` | Link to reproducible dataset, API, evaluation, and finalization scripts |
| `workspace` | Canonical runnable project; edit and execute files here |

## Work from the canonical path

```bash
cd /Users/gaurangbhatia/research/Agent_Safety_Research_Pack/10_Jev_Safe_Visual_Grounding/workspace
.venv/bin/python -m pytest -q
```

The original annotation exports and frozen labels are complete. For the new 180-task cohort, use the launchers and image root inside its extracted package as explained in README_FIRST.md.

For future Label Studio launches, use the workspace as the local-files document root:

```bash
cd /Users/gaurangbhatia/research/Agent_Safety_Research_Pack/10_Jev_Safe_Visual_Grounding/workspace
export LOCAL_FILES_SERVING_ENABLED=true
export LOCAL_FILES_DOCUMENT_ROOT="$PWD"
.label-studio-venv/bin/label-studio start --port 8081
```

The compatibility symbolic link preserves the old workspace path used during the original Label Studio work. This relocation record does not describe current server state.

## Next research actions

- Review the completed manuscript and same-data comparison.
- Give BLINDED_REVIEWER_AUDIT.zip to an independent human reviewer for the 100-case audit.
- Give FRESH_REAL_180_BLINDED_ANNOTATION.zip to two independent annotators. Each labels all 180 tasks; then adjudicate, freeze and version the new labels before a separate evaluation. The candidate categories are not human truth.
- Add authors/affiliations, target venue/template, declarations and reproducibility access details before submission.

The existing handoffs/JEV_ANNOTATOR_A_PACKAGE.zip and JEV_ANNOTATOR_B_PACKAGE.zip belong to the completed original annotation round.
