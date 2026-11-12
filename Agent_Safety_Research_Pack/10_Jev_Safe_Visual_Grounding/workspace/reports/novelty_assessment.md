# Formal novelty and gap assessment

## Decision: CONDITIONAL GO

Proceed only as a narrow empirical evaluation titled:

**When Not to Click: Stress-Testing Native Jev 1.14 Visual Decisions on Absent and Ambiguous GUI Targets**

The original “new joint gate” framing is a NO-GO. The candidate value is an independently annotated dataset and transparent stress test of the exact native hosted outputs under group-held-out UI layouts. The paper becomes viable only if real results show a reproducible answer that is not already subsumed by the closest benchmarks.

## Contributions already done

- Confidence-aware GUI grounding and abstention.
- Calibration and risk-coverage evaluation for grounding.
- Formal risk-control threshold selection under explicit assumptions.
- Negative-target/refusal benchmarks and one/many/none grounding.
- Count-localization consistency checks.
- Joint logistic/answerability gates and evidence-sufficiency analysis.
- Native Jev 1.14 Box localization and confidence calibration metrics.
- The product recommendation to ask Noul for presence and Choice for none/one/several beside Box.

These must be treated as prior work, not claimed contributions.

## Contributions partially studied

- Whether native TypeSafe probabilities and Box confidence add complementary information.
- Whether absent and genuinely ambiguous GUI targets should route to different recovery actions.
- Whether source-calibrated rejection thresholds retain useful coverage under unseen UI families.
- Whether calibration failures differ by absent, multiple, occluded, offscreen and unclear states.

## Candidate contributions not found in the verified literature

1. A human-reviewed benchmark centered on the exact native `jev-1.14.0` Noul + Choice + Box interface, with absent and ambiguous GUI targets kept distinct.
2. A frozen, group-held-out comparison of Box-only versus native semantic gates using both false-accept risk and useful automation coverage.
3. A documented analysis of how the native policy transfers across independently authored application/layout families, including latency, token cost, schema failures and recovery action.

These are hypotheses awaiting real execution, not current contributions.

## Strongest skeptical-reviewer rejection

“The paper combines a product-documented recipe with established selective prediction, evaluates it on a small synthetic benchmark and calls the integration novel. ImageJevBench already covers native Box calibration; Visual Jev already covers joint gating; PixelJev and Argus already frame transfer under shift; OpenRef and GUI refusal benchmarks already cover missing candidates. Without external applications, human labels, an independent baseline and real API results, this is an engineering report.”

That criticism is currently correct. The response is empirical rigor and a deliberately narrow claim, not stronger rhetoric.

## Cautious novelty statement permitted only after execution

If the final search and experiments still support it:

> To our knowledge, this is the first group-held-out empirical evaluation of native Jev 1.14 Noul, none/one/several Choice and Box outputs for click-or-abstain decisions on separately labelled absent and ambiguous GUI targets, under the reported dataset and protocol.

Do not use “first” until the external cohort, real calls and final adversarial search are complete. Current novelty confidence is **low-to-moderate (0.45)**: the exact combination was not found, but several sources nearly decompose it and the field is moving quickly.

## Final research questions

- RQ1: How accurately does native Jev identify visually absent targets?
- RQ2: How reliably does it distinguish one plausible match from several?
- RQ3: At a source-calibrated operating point, do presence and match-count outputs reduce false acceptance beyond Box confidence?
- RQ4: How do risk and coverage change on held-out layout families?
- RQ5: What latency, token use, monetary cost, failure rate and clarification burden result?

No additional research question is justified before the pilot.
