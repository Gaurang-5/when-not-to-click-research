# Academic submission execution plan

## Goal

Convert the completed synthetic Jev pilot into a credible academic paper using:

1. A human-revalidated ScreenSpot-v2-variants positive/absent cohort.
2. A newly collected cohort for multiple, occluded, offscreen, unclear, and difficult unique targets.
3. Frozen development, calibration, and confirmatory test evaluation.
4. Jev plus appropriate baselines.

The current synthetic test set is spent. It remains preliminary evidence and must not be used for further threshold selection.

## Proposed paper claim

The paper should test:

> Do native presence and match-count signals improve safe click-or-abstain decisions beyond localization confidence, and does combining those signals help beyond match count alone?

The paper should not claim that semantic gating is a new algorithm. The strongest pilot result was that uniqueness-only outperformed the more complex joint gates.

## Phase 0 — Lock the current pilot

**Status: complete.**

- Preserve the current 200-call Jev results.
- Preserve the frozen policy hash.
- Do not modify the old prompts or rerun the old test set for selection.
- Label all old results as synthetic pilot evidence.
- Use the pilot to motivate hypotheses and design, not as the final confirmatory result.

Deliverables already available:

- Final pilot report.
- Paper draft.
- Live metrics and figures.
- Frozen policy and checksum.
- ScreenSpot-v2-variants audit.

## Phase 1 — Resolve permissions and assign people

**Owner: research team. Target: 2–5 days.**

### Required people

- Annotator A.
- Annotator B.
- Adjudicator C.
- One dataset coordinator. The coordinator may be the adjudicator but must not copy labels between annotators.

Use anonymous IDs in released files. Keep a private record of who performed each role.

### Required permission work

Contact the ScreenSpot-v2-variants maintainer and request written confirmation covering:

- Academic use.
- Modification and human reannotation.
- Redistribution of images.
- Redistribution of derived annotations.
- Required attribution.

If image redistribution is not allowed, plan to release:

- Source IDs.
- Image hashes.
- Download/preprocessing scripts.
- Derived annotations.
- No copied images.

For newly collected screenshots, use demo accounts, synthetic content, public pages, or written permission. Do not capture private messages, student records, payment information, passwords, access tokens, medical information, or personal accounts.

### Proceed gate

Proceed with internal annotation while permission is pending, but do not publicly release the images until the licensing position is documented.

## Phase 2 — Build the ScreenSpot annotation pilot

**Owner: Codex prepares; research team annotates. Target: 3–5 days preparation.**

### Sampling

Select 75 unique screenshot groups:

- 25 desktop.
- 25 mobile.
- 25 web.
- Approximately balanced icon and text targets.
- Spread across visible application identities.
- Avoid near-duplicate screenshots.

For every screenshot create:

- One original positive instruction.
- One paired negative instruction.

Total: **150 annotation cases**.

### Preprocessing

For each image:

1. Pin the source revision.
2. Record original filename, dimensions, and SHA-256.
3. Resize deterministically if either side exceeds 1,568 pixels.
4. Preserve aspect ratio.
5. Scale the positive box by exactly the same factor.
6. Record processed dimensions and SHA-256.
7. Assign a neutral case ID that does not reveal positive or negative status.

Do not show annotators:

- Source positive/negative designation.
- Original `negative_action` or `negative_description`.
- Jev outputs.
- Model confidence.
- The other annotator's result.

### Pilot annotation

Each annotator independently records:

- Target status.
- Plausible visible match count.
- Safe reference action.
- Boxes for all visible plausible matches.
- Confidence.
- Defect flags.
- Short notes.

The adjudicator reviews only disagreements and defect flags.

### Pilot quality report

Calculate:

- Raw status agreement.
- Cohen's kappa when defined.
- Exact match-count agreement.
- Safe-action agreement.
- Box IoU for paired positive boxes.
- Disagreement counts by platform and instruction type.
- Negative cases relabelled as visible or ambiguous.
- Defective cases and exclusion reasons.

### Quality gate

Use these as review triggers, not universal validity rules:

- Raw status agreement target: at least 85%.
- Kappa target: at least 0.70.
- Match-count agreement target: at least 90%.
- Median matched-box IoU target: at least 0.80.
- Unresolved cases after adjudication: zero.

If the pilot fails these targets, revise the annotation manual and collect a new pilot. Do not quietly correct the existing labels and treat them as independent.

## Phase 3 — Freeze the annotation protocol

**Owner: Codex and research team. Target: 1–2 days.**

After the pilot:

- Clarify status definitions using observed disagreements.
- Freeze the annotation guide and version it.
- Freeze exclusion rules.
- Freeze box conventions.
- Freeze the list of safe actions.
- Preserve the first-round pilot labels.
- Document every rule changed after the pilot.

The final dataset must use the frozen version.

## Phase 4 — Build the full two-cohort dataset

**Owner: shared. Target: 2–4 weeks.**

### Cohort A — Reannotated ScreenSpot

Target:

- 300 unique screenshot groups.
- One positive and one candidate-negative instruction per screenshot.
- Approximately 600 cases.
- Balanced across desktop, mobile and web.
- Balanced as far as practical across icon and text targets.

Every negative must be independently verified. A negative that has a visible plausible match must be relabelled or excluded with a recorded reason.

### Cohort B — New challenge cases

Target:

- 400–600 cases.
- At least 20 independently identified applications.
- Prefer 30 applications.
- No more than two instructions per screenshot.
- Use synthetic/demo content.

Suggested status counts:

| Status | Target |
|---|---:|
| Difficult unique | 100–150 |
| Multiple | 100 |
| Occluded | 100 |
| Offscreen | 100 |
| Unclear | 100 |

Add absent cases only if needed for application balance; ScreenSpot already supplies many.

### Application-family identification

For every screenshot, record the actual application identity where possible. Do not use broad labels such as `windows` or `tool` as independent families. When identity is uncertain, group conservatively.

### Combined target

- Approximately 1,000–1,200 cases.
- Approximately 20–30 independently identified application families.
- Two independent annotations for every case.
- Adjudication for all disagreements.

## Phase 5 — Dataset quality control

**Owner: Codex. Target: 2–3 days.**

Automated checks:

- File presence and readable image format.
- Image size and SHA-256.
- Box bounds and non-degenerate geometry.
- Status/count/box consistency.
- Duplicate and near-duplicate screenshots.
- Repeated instructions.
- Source and license fields.
- Sensitive-data flags.
- Application-family completeness.
- Positive/negative pairs linked by screenshot group.

Manual review queues:

- Low-confidence annotations.
- Disagreement cases.
- Visually similar screenshots across applications.
- Generic repeated negatives such as `save` and `download`.
- Mixed-status cases.
- Uncertain application identity.

Output:

- Frozen adjudicated manifest.
- Exclusion ledger.
- Dataset card.
- Agreement report.
- Source/license ledger.

## Phase 6 — Statistical design and sample-size decision

**Owner: Codex; research team approves before model collection. Target: 2–3 days.**

Use the annotation pilot and synthetic Jev pilot to define the new protocol. Do not use confirmatory test outputs.

### Recommended primary comparisons

1. Uniqueness-only Choice gate versus Box-confidence gate on multiple-target acceptance.
2. Joint gate versus uniqueness-only gate on useful unique-target automation.

### Recommended primary outcomes

- Multiple-target incorrect acceptance.
- Correctly accepted unique targets.

Report absent, occluded, offscreen, and unclear results as prespecified category endpoints. Correct for multiple primary tests.

### Required power work

Estimate the required number of independent application clusters using:

- Expected discordant paired outcomes.
- Cluster sizes.
- Application-level variation.
- Desired power.
- Multiplicity correction.

Do not count screenshot variants as independent applications. If sample-size requirements exceed the available applications, describe the work as an exploratory benchmark rather than a confirmatory safety study.

## Phase 7 — Split without leakage

**Owner: Codex.**

Split entire application families, never individual rows.

Preferred split with 30 families:

- Development: 12 families, about 40%.
- Calibration: 6 families, about 20%.
- Test: 12 families, about 40%.

With 20 families:

- Development: 8.
- Calibration: 4.
- Test: 8.

Keep together:

- All cases from one application family.
- All instructions from one screenshot.
- Positive/negative pairs.
- Near-duplicate screens.

Balance status, platform, icon/text, target size, and difficulty across splits as far as whole-family assignment permits. Publish a leakage audit.

## Phase 8 — Select and implement baselines

**Owner: Codex.**

Required policies:

- Accept every valid Box.
- Box-confidence threshold.
- Presence-only.
- Uniqueness-only.
- Presence + Box.
- Presence + uniqueness + Box.
- Logistic joint gate.

Required external comparison:

- At least one independently developed GUI-grounding model that can return a point/box and abstain or be paired with an explicit rejection prompt.

Use the same processed images, instructions, correctness criteria, and splits. Record model revision, prompt, decoding settings, hardware/API, cost, latency, and failures.

Do not treat a baseline's inability to abstain as missing data. Its forced click remains an attempted action.

## Phase 9 — Freeze before confirmatory testing

**Owner: Codex; research team signs off.**

Freeze and hash:

- Dataset manifest.
- Image files.
- Human adjudications.
- Split assignments.
- Model versions.
- Prompts.
- Parser.
- Policy definitions.
- Development fit.
- Calibration thresholds.
- Outcomes and denominators.
- Statistical tests.
- Exclusion rules.
- Analysis code.

Write a dated protocol and optionally preregister it publicly. After freezing, no one should inspect confirmatory test predictions until collection finishes.

## Phase 10 — Run models in order

**Owner: Codex; API key remains local.**

Order:

1. Smoke test development examples.
2. Collect complete development outputs.
3. Fit permitted models.
4. Collect calibration outputs.
5. Select operating thresholds.
6. Freeze hashes.
7. Collect test outputs once.
8. Analyze using frozen code.

Failed calls remain in denominators and fail closed. Retry only documented transient service errors under a prespecified cap. Never repair malformed boxes silently.

### Jev cost estimate

The completed pilot cost about $0.0192 for 200 cases, approximately $0.000096 per case.

At the same usage:

- 1,000 Jev cases: about $0.096.
- 1,200 Jev cases: about $0.115.
- A 20% operational reserve would keep expected Jev spend below about $0.14.

Actual cost depends on image tokenization and returned usage. External baseline compute/API cost is separate. Human annotation will be the dominant resource.

## Phase 11 — Final analysis

**Owner: Codex.**

Produce:

- Frozen policy table.
- Category-specific false-accept rates.
- Selective risk and marginal incorrect-action rate.
- Useful unique-target automation.
- Localization IoU and center-containment accuracy.
- Risk–coverage curves.
- Calibration and reliability plots.
- Application-cluster confidence intervals.
- Paired clustered hypothesis tests.
- Multiplicity-adjusted p-values.
- Family-specific results.
- Leave-one-family-out sensitivity.
- Cost, latency, failures, and retries.
- Error taxonomy with representative licensed screenshots.

Zero observed errors must include uncertainty bounds and must never be described as proof of safety.

## Phase 12 — Write and package the submission

**Owner: shared. Target: 1–2 weeks.**

Paper sections:

1. Problem and motivation.
2. Related work and narrow novelty claim.
3. Dataset and annotation protocol.
4. Model interface and frozen policies.
5. Experimental design.
6. Confirmatory results.
7. Error analysis.
8. Limitations and ethics.
9. Conclusion.

Release package:

- Paper.
- Dataset card.
- Annotation guide.
- Agreement report.
- Source and license ledger.
- Frozen manifests and hashes.
- Evaluation code.
- Redacted model logs.
- Statistical tables.
- Figures.
- Reproduction instructions.

If image redistribution is restricted, release annotations, hashes, IDs, and preparation scripts instead of copied screenshots.

## Suggested schedule

| Week | Work |
|---|---|
| 1 | Permissions, annotator assignment, ScreenSpot pilot preparation |
| 2 | Independent pilot annotation and adjudication |
| 3 | Agreement analysis, manual revision, protocol freeze |
| 4–6 | Full ScreenSpot reannotation and challenge-case collection |
| 7 | Dataset validation, fine application grouping, split and power analysis |
| 8 | Baseline implementation, development and calibration |
| 9 | Freeze and one-time confirmatory test |
| 10 | Statistics, plots and error analysis |
| 11–12 | Paper writing, internal review and submission formatting |

This schedule assumes annotators are available in parallel. Collection and adjudication may take longer.

## Immediate next actions

### Research team

1. Assign Annotator A, Annotator B and Adjudicator C.
2. Contact the ScreenSpot-v2-variants maintainer about license and redistribution.
3. Confirm that the team can annotate 150 pilot cases.
4. Confirm whether desktop, mobile and web screenshots are all in scope.
5. Do not download and label cases informally before the blinded package is created.

### Codex

After the team confirms the above:

1. Build the pinned ScreenSpot downloader.
2. Select 75 stratified screenshot groups.
3. Resize and hash images.
4. Transform positive boxes.
5. Generate blinded Annotator A and B packages.
6. Generate the adjudication package.
7. Add validation and agreement scripts.

## Stop conditions

Pause expansion and repair the study design if:

- ScreenSpot licensing cannot be clarified.
- Annotators see model predictions or each other's labels.
- Application identity cannot be recovered well enough to avoid leakage.
- Agreement is poor after one manual revision.
- Sensitive information cannot be removed.
- The planned number of independent application families is unattainable.
- Confirmatory test data are viewed before policy freeze.

These conditions do not invalidate the completed synthetic pilot; they limit the claims available for the academic submission.
