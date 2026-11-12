# Planned code structure

The research implementation is a future milestone; this folder contains no implemented or tested benchmark.

Suggested modules:
- adapters: Jev, probabilistic LLM judge, TF-IDF classifier and rules.
- data: schema validation, family split manifest and provenance checks.
- calibration: source fitting and separately budgeted target adaptation.
- evaluation: metrics, family bootstrap intervals and paired comparisons.
- plots: reliability, safety–coverage and label-budget figures.
- configs: fixed policy, prompts, model IDs and run seeds.
- tests: hand-calculated metrics, all-allow/all-block behavior, failed calls and leakage checks.

Do not embed API keys. Pin dependencies and record every model version. Offline scoring must never execute the proposed actions in the dataset.
