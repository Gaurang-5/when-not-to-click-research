# Reviewer-response implementation ledger

Original raw calls, final labels and frozen policies remain unchanged. The expanded design was written after inspection of the real-interface outcomes, so split-based results remain exploratory.

| Request | Implemented evidence | Remaining |
|---|---|---|
| Independent model | Pinned local Qwen2.5-VL-7B collector, exact prepared inputs, strict output checks and deployment metadata | Complete:951 inputs; matched hashes, geometry/semantic-gate metrics and paired source-cluster intervals |
| Base model vs gate | Strict/IoU0.3/center localization and Brier skill, real-only | No causal claim that gates alone explain failure |
| Human box ceiling | 98 real cases unique for both annotators: IoU and directional center agreement | Agreement is a conditional reference, not a true ceiling |
| Real recalibration | Source-cluster 40/30/30 split, fit-only logistic diagnostic, empirical and exact-binomial LTT threshold selection | No threshold qualifies at 10% risk; do not tune on test to force success |
| Label sensitivity | A-only, B-only, final and original-consensus-only metrics | Independent 100-case human audit |
| Balanced real extension | 180 blinded candidate tasks /60 unused ScreenSpot-Pro images, source/pixel duplicate rejection | Two human passes, adjudication, freeze; final class balance unknown |
| Ranking | AUROC and tie-aware AURC, 1,000 source-cluster resamples | Complete:paired model geometry intervals and A/B/final/consensus-only sensitivity |
| Repeats/prompts | Frozen 4,506-call additional Jev protocol with no automatic retries | Completed:4,506 attempts; seven complete pass/variant cohorts including original |
| Fragile significance | Exploratory p=0.0476 no longer carries a central claim | None |
| Standard math | Utility framed as textbook; Brier skill and LTT formula added | No mathematical novelty claim |
| Related work | Selective classification, LTT, CRC, Qwen, ScreenSpot-Pro, UI-TARS cited | Venue-specific literature update |
| Cost | Input and free output rate stated; raw malformed-response usage included | Provider invoice is not available; local energy/hardware unpriced |
| Writing | Concise abstract; real-only result first; mixed/published context moved to appendices | Complete final pass on all planned collection logs; human audit remains |

Files: reviewer_analysis_summary.json is the executed offline summary; CSVs retain all denominators. collection_summary.json is a timestamp-sensitive snapshot, not proof that a process is still running. Never replace human labels with source candidate categories or model output.
