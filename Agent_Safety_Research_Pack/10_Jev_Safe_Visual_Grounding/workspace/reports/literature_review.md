# Literature review: safe GUI grounding and Jev 1.14

Search and verification date: 17 October 2026. The machine-readable matrix is `literature_matrix.csv` (17 entries, 27 fields). Important Jev-specific sources are analyzed separately in `jev_competitors.md`.

## Method and overlap scale

The review used arXiv/full HTML or PDFs where available, official conference/project pages, official TypeSafe documentation, repositories and downloadable dataset schemas. It searched the seed titles and adjacent terms covering absent targets, ambiguity, refusal, selective prediction, calibration, risk control and cross-interface transfer. Publication status is conservative: a preprint is not called peer reviewed unless an official venue listing was verified. “Not established” means the inspected source did not support the requested property; it does not prove the property never exists.

Overlap scores are descriptive reading aids, not novelty verdicts:

- 0: unrelated method/problem.
- 1: shares generic GUI grounding or calibration context.
- 2: shares one central axis such as negative targets, uncertainty or shift.
- 3: shares two central axes or a closely related evaluation.
- 4: directly threatens a major proposed contribution.
- 5: appears to answer the same model/output/task/shift question end to end.

No inspected source was assigned 5. The absence of a 5 is not proof of priority.

## Closest competitors

### SafeGround

[SafeGround](https://arxiv.org/abs/2602.02419) derives spatial uncertainty from repeated grounding samples and calibrates rejection thresholds for accepted-error control on ScreenSpot-Pro. It establishes uncertainty-aware abstention and formal risk calibration for GUI grounding. It does not establish a native Jev 1.14 presence/count/Box evaluation or a dedicated absent-and-ambiguous template-held-out test. The proposed study may compare signals, but cannot claim GUI grounding risk calibration as new.

### Argus

[Argus](https://arxiv.org/abs/2606.25760), accepted at NeurIPS 2026 according to the official conference listing checked during this review, compares many uncertainty methods across VLMs and GUI grounding datasets. Its core result is directly relevant: uncertainty rankings and conformal behavior need not transfer across interfaces. This weakens any broad “unseen-template risk guarantee” claim and makes empirical transfer degradation a central outcome.

### HyperClick and SAVOR

[HyperClick](https://arxiv.org/abs/2510.27266) trains GUI grounding confidence with a self-critique/reward design; [SAVOR](https://arxiv.org/abs/2609.16601) trains self-aware visual grounding and reports calibration/selective-risk metrics for hallucination-oriented tasks. They show learned confidence and selective prediction are established ideas. Neither is the same as post-hoc evaluation of native Jev image primitives.

### OpenRef, OSWorld-G/Jedi, MEGA-GUI and GroundGUI

[OpenRef](https://arxiv.org/abs/2605.25706) explicitly covers one/many/none targets and uses count-localization consistency. [OSWorld-G/Jedi](https://arxiv.org/abs/2505.13227) includes refusal cases; [MEGA-GUI](https://arxiv.org/abs/2511.13087) has a feasibility/refusal stage; [GroundGUI](https://arxiv.org/abs/2610.19100) describes ScreenRef refusal scenarios. Negative-target and refusal evaluation therefore already exist in GUI grounding. A Jev paper must distinguish native-output calibration, absent versus ambiguous recovery actions and group-held-out policy behavior.

### CORA and general risk control

[CORA](https://arxiv.org/abs/2604.09155) uses conformal calibration for execute/abstain mobile GUI actions and reports safety/helpfulness/interruption trade-offs. Its displayed loss multiplies harm by execution and averages over all cases; this is a marginal harmful-execution rate, not automatically risk conditional on accepted actions. The proposed protocol reports both denominators. [Learn then Test](https://arxiv.org/abs/2110.01052) establishes finite-sample risk-control methodology under its assumptions. Neither method licenses guarantees after arbitrary distribution shift.

### Visual Jev, PixelJev and ImageJevBench

[Visual Jev](https://arxiv.org/abs/2609.25845) already compares confidence and logistic gates using margin, entropy and answerability, with frozen calibration and selective metrics. It is based on Qwen3-VL rather than hosted native Jev 1.14 and is not a GUI absent/ambiguous template-transfer experiment.

[PixelJev](https://arxiv.org/abs/2609.29283) explicitly proposes separating correctness, candidate availability and evidence sufficiency, freezing thresholds and testing under shift. The broad conceptual agenda is therefore already articulated.

[ImageJevBench Box methodology](https://github.com/fstandhartinger/jevbench/blob/main/datasets/imagejev-box-v0.1/METHOD.md) already evaluates native Jev 1.14 Box localization, IoU, Acc@0.5/0.75, confidence ECE, latency and cost, including UI images. Its public 300-item schema has one gold box per item and does not supply the required absent/ambiguous decision study. “First Jev Box calibration” is not defensible; “absent/ambiguous native-output policy transfer” remains a candidate empirical distinction.

## Other verified lessons

- [UI-Zoomer](https://arxiv.org/abs/2604.14113) routes uncertainty to adaptive zoom; uncertainty can trigger recovery rather than only abstention.
- The V2P seed ID `2601.06899` was withdrawn/replaced; the reviewed canonical preprint is [arXiv:2508.13634](https://arxiv.org/abs/2508.13634). It calibrates visual attention, not output probabilities.
- [RecAgent](https://arxiv.org/abs/2508.04025) includes component recommendation and human clarification for perceptual/decision uncertainty.
- [GUI-Primitives](https://arxiv.org/abs/2608.21832) diagnoses relational spatial reasoning using controlled candidate pairs. Its contrastive candidates are not the same as an instruction with no unique intended target.
- [AgroVG](https://arxiv.org/abs/2605.22034) evaluates one/many/none in agriculture, demonstrating that empty and set-valued grounding metrics are established outside GUIs.
- [IGG](https://igg-bench.github.io/) describes 601 interactive visibility-constrained tasks across 16 mock applications, but its paper/data were marked unavailable on the inspected project page. Hidden/recoverable states should not be collapsed into absence.

## Answers to the formal novelty questions

1. Native image presence, match count and Box together: official TypeSafe documentation already prescribes the combination; small implementations exist. A comprehensive published evaluation was not verified.
2. These native outputs for absent and ambiguous GUI targets: no complete study was verified, but adjacent refusal/open-world benchmarks are strong overlap.
3. Calibration of their joint scores for click/abstain: Visual Jev evaluates joint gating conceptually, but not the exact native hosted trio in this GUI setting. The method itself is not new.
4. Transfer of a frozen native policy to unseen application templates: not verified end to end; Argus and PixelJev strongly anticipate the transfer question.
5. False-click risk and useful coverage: established generally by SafeGround/CORA/selective-prediction work; not verified for the exact native outputs and target categories.
6. All exact elements in one executed study: not found in the bounded search. This supports only a cautious candidate gap, not a priority claim.

## Review limitations

This was a broad current review, not a systematic review with dual screeners. Google Scholar was not directly available. GroundGUI was metadata/abstract screened rather than fully reviewed. IGG's paper and data were unavailable. Some 2026 works may change venue status or release revisions. Repository searches are inherently incomplete, and an unpublished internal evaluation could exist.
