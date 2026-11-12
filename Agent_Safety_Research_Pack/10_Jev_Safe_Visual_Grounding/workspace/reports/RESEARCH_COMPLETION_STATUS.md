# Research execution and manuscript status

Updated 23 October 2026. This status supersedes earlier completion claims.

## Completed evidence

- Original 200-call synthetic pilot, frozen policies, and held-out synthetic evaluation.
- Two human exports over 951 cases, reviewer-approved B resolution on 259 flags, frozen labels.
- Original external collection: 951 post-credential responses, 940 valid and 11 fail-closed. Its raw log remains immutable.
- Provenance audit: 200 exact reused pilot cases, including fitting/calibration material. Real-only evaluation has 751 cases.
- Real frozen-policy results: B 45 accepts/28 errors; D 26/16; E 1/0. Strong mixed-cohort transfer claims withdrawn.
- Raw-response accounting: 3,199,297 input/73,284 output tokens. Rate estimate $0.134370474; output tokens free at the recorded provider rate.
- Cluster intervals and tests, subgroup diagnostics, calibration, entropy controls, curves and standard utility framing.
- Reviewer expansion: A-only/B-only/final/consensus-only label sensitivity; strict/IoU0.3/center scoring; conditional human geometry agreement; Brier skill; AUROC/AURC with cluster intervals.
- Exploratory real-cluster fit/calibration/test analysis: real fitting improves test Brier loss, but empirical calibration-risk selection and LTT find no qualifying threshold at the fixed 10% accepted-error target. Empty accepts have undefined risk.
- Rewritten main results and abstract; selective-classification/LTT/CRC and GUI-model related work; executed diagnostics integrated into PDF/TeX.
- Two private blinded human packages: 100-case audit, and 180 new ScreenSpot-Pro candidate tasks on 60 unused screenshots. No human completion is claimed for either.

## Collection status

- Jev repeat/prompt collection COMPLETE: 4,506 distinct planned attempts; 4,439 valid responses and 67 failures (44 box geometry, 20 probability sums, 3 HTTP 529). All attempts remain in denominators. No repeats or retries are needed. Additional usage: 16,457,448 input/346,928 output tokens; rate estimate $0.691212816. Five original passes plus both prompt variants are fully evaluated. Raw-log SHA256: acee74d5517e6f0936f20f698270ba6395c4b1617a3e4d252648c86df26b0ba9.
- Independent model COMPLETE: 951 distinct Qwen inputs, 889 valid/62 fail-closed geometry outputs. All 951 image hashes match Jev; model/protocol digests are unchanged across the resumed run. Primary real 751 results: Jev 41/131 versus Qwen 22/131 strict localizations; center-only 77/131 versus 67/131. Paired source-cluster intervals, alternative-label sensitivity and per-case ledgers are saved. No new API calls are needed for these analyses.
- Mean full-response latency on matched 951: Jev 0.459s, local Qwen 11.339s. Qwen API charge was zero; local hardware/electricity is unpriced. Different deployments prevent a hardware-normalized speed claim.
- Qwen raw-log SHA256: a42bd571da31342832f3939d09abae43a594b3894cfcd2686c954aa284d2c0e7. Both new raw logs are now frozen with checksum sidecars.
- Exact collection snapshot: results/iteration3/collection_summary.json. Refresh via scripts/evaluate_iteration3_collection.py; partial passes never produce headline metrics.

## Human and submission requirements

Two independent annotators must complete all 180 new tasks, followed by adjudication, label freeze and a separately versioned evaluation. The existing 100-case audit also needs an independent human reviewer. Candidate construction counts are not true class balance.

All planned automated collections and saved-data analyses are complete. The manuscript is rebuilt from completed evidence; human work remains as described above. Add authors/affiliations, target venue/template, declarations, source-image privacy/license review, and public code/data access URL. The paper remains a research draft and supplies no deployment safety guarantee.
