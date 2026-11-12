# Human GUI Grounding Dataset Collection Brief

## Purpose

We are building a research dataset to evaluate whether a visual grounding model should **click, ask for clarification, request another view, or abstain** when a requested GUI target is unique, absent, duplicated, occluded, offscreen, or visually unclear.

The model must not be shown to annotators. Human labels must be created before any final model evaluation.

## Collection targets

### Approved external source

ScreenSpot-v2-variants may provide a reannotated positive/absent cohort. Follow `SCREENSPOT_V2_VARIANTS_AUDIT.md`: use only the original positive instruction and short negative instruction as annotation candidates, keep all rows from one image together, resize before labelling, and obtain two independent human labels. It cannot supply the multiple, occluded, offscreen, or unclear categories.

### Stage 1: annotation pilot

- 100–150 cases.
- At least five genuinely different applications or websites.
- At least two distinct screens or workflows per application.
- Two independent annotators per case.
- One adjudicator for disagreements.

This stage checks whether the instructions and labels are understandable. Do not use this pilot as the final confirmatory test if the annotation rules or prompts change afterward.

### Stage 2: paper dataset

- Target 800–1,200 cases.
- Target 20–30 independent application or website families.
- Prefer 30 families with about 40 cases each.
- No application family may appear in more than one development/calibration/test split.
- Avoid creating most of the dataset from color, theme, or position variants of one interface.

A useful per-application target is:

| Status | Suggested cases |
|---|---:|
| Unique | 15 |
| Absent | 5 |
| Multiple | 5 |
| Occluded | 5 |
| Offscreen | 5 |
| Unclear | 5 |
| **Total** | **40** |

This deliberately over-samples difficult negative cases. It does not represent natural usage prevalence, so the paper must report category-specific results and must not present the aggregate rate as a deployment prevalence estimate.

## Unit of data

One **case** is:

1. One final screenshot.
2. One natural-language target instruction.
3. The application and screen from which it came.
4. Two independent annotations.
5. Zero or more pixel-coordinate target boxes.
6. A safe reference action.

The same screenshot may be reused for at most two instructions. If reused, assign the same `screenshot_group_id` so the cases remain together during splitting and statistical resampling.

## Applications and screens

Use a varied set of interfaces, such as:

- Productivity and document tools.
- E-commerce and booking pages.
- Email and messaging interfaces with synthetic accounts.
- Dashboards and analytics tools.
- Settings and administration pages.
- Learning platforms.
- Media and design tools.
- Desktop applications.
- Mobile interfaces, kept as a distinct source family.

Do not collect bank accounts, medical records, private conversations, real student records, passwords, API keys, payment details, or other sensitive information. Use demo accounts or synthetic content.

Each `application_family_id` must represent one application or one strongly related design system. A theme change or a different account does not create a new family.

## Screenshot requirements

- Format: PNG preferred; JPEG accepted.
- Final image dimensions: each side must be between 280 and 1,568 pixels.
- Maximum file size: 16 MiB.
- Record exact width and height.
- Keep browser zoom, display scale, viewport size, and device type consistent within a capture session.
- Capture the complete visible viewport.
- Do not draw boxes, arrows, labels, cursors, or annotations onto the original screenshot.
- Do not resize, crop, or compress an image after annotators create boxes.
- If preprocessing is required, create the final research image first and annotate that exact file.
- Preserve an SHA-256 hash for every final image.
- Remove or replace personal information before annotation.

Recommended desktop capture size: 1,000 × 700 or another fixed size that preserves readable interface text.

## Target instructions

Instructions should sound like plausible user requests:

- “Click Export.”
- “Open notification settings.”
- “Select the Premium plan.”
- “Click the Submit button in the invoice dialog.”

Instructions must not reveal the answer through coordinates or annotations. Avoid phrases such as:

- “Click the button at the top right.”
- “Click the element inside the red box.”
- “Click the only visible button,” unless uniqueness itself is part of the natural task.

Record the exact instruction shown to every annotator and model. Do not silently rewrite it after annotation.

## Mutually exclusive target statuses

Construct cases so that one primary status clearly applies. Cases combining several unresolved phenomena should be adjudicated or excluded before model evaluation.

### `unique`

Exactly one visible, sufficiently identifiable, actionable element matches the instruction. The annotator can provide one complete click box.

Reference action: `click`.

### `absent`

The requested element does not exist in the captured application state. It is not merely outside the viewport or covered by another window.

Reference action: `abstain` or `clarify`, depending on the instruction.

### `multiple`

Two or more visible, actionable elements plausibly match the instruction, and the wording does not identify one of them.

Reference action: `clarify`.

Every plausible match receives a separate box.

### `occluded`

The intended target exists at the current screen location but is partly or fully covered by a menu, dialog, tooltip, overlay, or another window. It cannot safely be clicked from the current pixels.

Reference action: `uncover` or `abstain`.

Annotate the visible portion only if the project lead has confirmed that a visible box is meaningful; otherwise provide no click box and explain the obstruction in notes.

### `offscreen`

The target is known to exist in the current application state but is outside the captured viewport and requires scrolling, paging, or navigation.

Reference action: `scroll` or `navigate`.

No target box is drawn because the element is not visible.

### `unclear`

Something potentially relevant is visible, but blur, clipping, tiny text, low contrast, truncation, or ambiguous wording prevents reliable identification.

Reference action: `zoom`, `request_better_view`, or `clarify`.

Do not use `unclear` merely because the annotator is uncertain about the instructions. Flag instruction defects separately.

## Target boxes

Use pixel coordinates on the final image:

`[left, top, right, bottom]`

Rules:

- Origin `(0,0)` is the top-left image corner.
- `left < right <= image_width`.
- `top < bottom <= image_height`.
- Coordinates may be integers.
- Draw the visible interactive hit region, not the surrounding card or entire window.
- Include one row per plausible target.
- Unique cases normally have exactly one box.
- Multiple cases must have at least two boxes.
- Absent and offscreen cases have no boxes.
- Never invent hidden geometry for a fully occluded element.

## Safe reference actions

Use one of:

- `click`
- `clarify`
- `scroll`
- `navigate`
- `uncover`
- `zoom`
- `request_better_view`
- `abstain`

Only a `unique` case may normally receive `click`.

## Annotation procedure

### Annotator A and Annotator B

Each case must be labelled independently.

Annotators must not see:

- Jev responses or confidence scores.
- Predictions from any comparison model.
- The other annotator’s answers.
- The procedural or intended label used by the case creator.

Each annotator records:

- Primary target status.
- Visible plausible-match count.
- Safe reference action.
- Boxes for every visible plausible match.
- Confidence: `high`, `medium`, or `low`.
- A short note for difficult cases.
- Whether the instruction or screenshot is defective.

Do not ask annotators to force an answer when the case is defective. Mark `needs_review=true`.

### Adjudicator C

The adjudicator reviews only:

- Status disagreements.
- Match-count disagreements.
- Box disagreements.
- Different safe actions.
- Any case marked `needs_review`.

The adjudicator must preserve the two original labels and record:

- Final adjudicated status.
- Final match count.
- Final safe action.
- Final boxes.
- Reason for the decision.
- Whether the case should be included or excluded.

Exclusion is allowed only for corrupt images, invalid geometry, broken instructions, licensing problems, or unresolved human ambiguity. Never exclude a case because a model failed on it.

## Source and licensing requirements

For every application family, record:

- Application or website name.
- Version or capture date.
- Source URL when applicable.
- Screenshot owner.
- License or written permission.
- Whether redistribution of images is allowed.
- Required attribution.
- Account type: demo, synthetic, public, or private.
- Confirmation that sensitive information was removed.

If screenshots cannot legally be redistributed, mark them clearly. They may be unsuitable for an open benchmark even if aggregate evaluation is allowed.

## Required files

```text
human_dataset/
├── images/
│   ├── app01_0001.png
│   └── ...
├── cases.csv
├── annotations.csv
├── boxes.csv
├── sources.csv
└── README.md
```

### `cases.csv`

One row per screenshot-instruction case.

Required columns:

- `case_id`
- `screenshot_group_id`
- `image_filename`
- `application_family_id`
- `application_name`
- `screen_or_workflow`
- `instruction`
- `width`
- `height`
- `image_sha256`
- `capture_date`
- `device_type`
- `source_id`
- `creator_intended_status`
- `notes`

`creator_intended_status` is for dataset administration only. It must be hidden from annotators and never replace human labels.

### `annotations.csv`

One row per annotator per case.

Required columns:

- `case_id`
- `annotator_id`
- `annotation_round`
- `target_status`
- `plausible_match_count`
- `safe_action`
- `confidence`
- `needs_review`
- `instruction_defect`
- `image_defect`
- `notes`
- `annotated_at`

### `boxes.csv`

One row per box. A case with no visible match has no box rows.

Required columns:

- `case_id`
- `annotator_id`
- `annotation_round`
- `box_index`
- `left`
- `top`
- `right`
- `bottom`
- `box_note`

Use annotator ID `ADJUDICATED` for final boxes.

### `sources.csv`

One row per source or application family.

Required columns:

- `source_id`
- `application_family_id`
- `application_name`
- `source_url`
- `version_or_capture_date`
- `owner`
- `license_or_permission`
- `redistribution_allowed`
- `attribution_required`
- `account_type`
- `sensitive_data_removed`
- `notes`

## Naming rules

- Use stable IDs; never use a person’s name.
- Example application family: `app_07_calendar`.
- Example screenshot group: `app07_settings_003`.
- Example case: `app07_settings_003_notifications`.
- Do not encode the true target status in filenames visible to annotators.

## Quality-control checks

The research team will reject or return cases with:

- Missing or unreadable images.
- Dimensions outside the supported range.
- Incorrect image hashes.
- Boxes outside image bounds.
- Unique cases without exactly one usable box.
- Multiple cases with fewer than two boxes.
- Absent or offscreen cases with click boxes.
- Duplicate or near-duplicate screenshots crossing splits.
- Application-family leakage across splits.
- Missing license or permission information.
- Personal or sensitive information.
- Annotators who saw model outputs.
- Labels copied between annotators.

## Information to send with the first batch

Send:

1. The `human_dataset` folder or a ZIP archive.
2. Names or anonymous IDs of the two annotators and adjudicator.
3. Confirmation that annotations were independent.
4. Confirmation that nobody saw model predictions.
5. Description of how screenshots were captured.
6. Permission/license information for every source.
7. Any known uncertainties or collection deviations.

Do **not** send API keys, passwords, session cookies, private account exports, or credentials.

## What happens after delivery

The research pipeline will:

1. Validate files, hashes, geometry, labels, licenses and duplicates.
2. Calculate raw agreement, Cohen’s kappa where defined, count agreement and box overlap.
3. Produce a disagreement/adjudication queue.
4. Freeze the adjudicated dataset.
5. Split by application family without leakage.
6. Prespecify hypotheses, policies, thresholds and sample-size analysis.
7. Collect development and calibration model outputs.
8. Freeze policy hashes.
9. Collect the untouched confirmatory test once.
10. Produce statistics, error analysis, figures, paper tables and a reproducibility package.

The present synthetic test set will not be reused for new threshold tuning.
