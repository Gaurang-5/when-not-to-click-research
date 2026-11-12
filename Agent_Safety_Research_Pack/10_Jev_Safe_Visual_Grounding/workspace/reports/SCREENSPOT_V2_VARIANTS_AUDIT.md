# ScreenSpot-v2-variants suitability audit

**Audit date:** 17 October 2026  
**Dataset:** [likaixin/ScreenSpot-v2-variants](https://huggingface.co/datasets/likaixin/ScreenSpot-v2-variants)  
**Pinned repository revision:** `aa4d83b`

## Decision

**Use it as a human-revalidated external cohort, not as the complete paper dataset.**

ScreenSpot-v2-variants is highly relevant because it pairs existing positive grounding instructions with a negative instruction described by the authors as an operation that cannot be done in the screenshot. It can supply realistic positive and candidate-absent examples across desktop, mobile and web screenshots. It does not contain verified multiple, occluded, offscreen or unclear labels, and its negative annotations lack the metadata needed to treat them as independently human-verified ground truth.

## What the official repository contains

The dataset card describes four instruction styles:

- `instruction`: original ScreenSpot instruction.
- `action`: a more explicit action.
- `description`: target UI description.
- `negative`: an operation that cannot be done in the screenshot.

The repository contains 755 image files according to the Hugging Face viewer and three annotation files. The raw annotation audit found:

| Platform file | Annotation rows | Referenced images | Coarse application labels | Icon rows | Text rows |
|---|---:|---:|---:|---:|---:|
| Desktop | 334 | 231 | 3 | 140 | 194 |
| Mobile | 501 | 248 | 3 | 211 | 290 |
| Web | 437 | 251 | 4 | 203 | 234 |
| **Total** | **1,272** | **730** | **10** | **554** | **718** |

The original positive set therefore contains 1,272 instruction-target rows over 730 referenced images. Each row also contains a negative instruction, yielding up to 1,272 candidate negative cases. These are paired observations on reused screenshots, not 2,544 independent screenshots.

Images carry between one and five positive annotation rows:

| Rows per image | Image count |
|---:|---:|
| 1 | 372 |
| 2 | 216 |
| 3 | 108 |
| 4 | 26 |
| 5 | 8 |

All instructions from the same image must remain in the same dataset split and bootstrap cluster.

## Raw schema

Every audited annotation row contains:

- `id`
- `img_filename`
- `img_size`
- `bbox`
- `instruction`
- `action`
- `decription` — misspelled in the source
- `negative_instruction`
- `negative_action`
- `negative_description`
- `application`
- `platform`
- `ui_type`

Positive boxes are valid absolute-pixel `[left, top, right, bottom]` coordinates. Negative rows have no box, which is appropriate for a candidate-absent target.

Annotation-file hashes:

- Desktop: `0d5e26205dcf892c7091c1846da6602b8f9c36c619353e8266cbf7cc8e97b895`
- Mobile: `2cd380d210c4ec691a83b8799c9c9a1c2514e63442aaec38283d62a37b3ccf66`
- Web: `228686e851b02ef94f72a2b84c70891357a2b9c61c51fda9d1e02acfe6744bc4`

## Important limitations

### Negative instructions need human verification

The official card says the negative operation cannot be performed, but the repository does not state that two independent annotators verified target absence. The raw fields often describe a specific nonexistent element, for example a colored download or save button at a claimed location. Those descriptions may be synthetic distractors rather than observations of the pixels.

For our study:

- Use `negative_instruction` as the candidate instruction.
- Do not use `negative_action` or `negative_description` as ground truth.
- Have two annotators independently verify that no plausible visible target exists.
- Exclude or relabel negatives where a plausible match is visible.
- Preserve disagreements and adjudication.

### It covers only part of our taxonomy

The dataset can support:

- `unique`, after revalidating the positive target and box.
- `absent`, after revalidating each negative instruction.

It does not provide reliable ground truth for:

- `multiple`
- `occluded`
- `offscreen`
- `unclear`

Those categories still require a supplementary collected cohort.

### Application identity is too coarse

The `application` field contains only ten broad platform/category labels such as `windows`, `macos`, `ios`, `android`, `shop`, `tool`, `forum`, and `gitlab`. These are not necessarily independent application families. Human review must add a finer `application_family_id` from visible application identity and provenance. Unknown identities should be grouped conservatively rather than guessed.

### Image resizing is required for Jev

Of 730 referenced images, 566 have at least one side larger than Jev's 1,568-pixel limit. A deterministic preprocessing step must:

1. Preserve aspect ratio.
2. Scale the longest side to at most 1,568 pixels.
3. Keep the other side at least 280 pixels.
4. Apply the identical scale to positive bounding boxes.
5. Store original and processed hashes and dimensions.
6. Complete preprocessing before human box review and API calls.

### Negative instructions are repetitive

There are 626 unique normalized negative-instruction strings across 1,272 rows. Generic requests are repeated heavily: `save` appears 148 times, `add to favorites` 50 times and `download` 40 times. Results must therefore be clustered by screenshot and analyzed by instruction family; random row-level splitting would leak linguistic patterns.

### Licensing needs clarification

The variant repository currently has missing/empty YAML metadata and does not display a license. The linked OS-Copilot ScreenSpot-v2 repository displays Apache-2.0, and the linked evaluation code is MIT, but neither automatically proves redistribution rights for every image in the variants repository. Before releasing a derived benchmark:

- Contact the dataset maintainer for written license clarification.
- Preserve upstream attribution and revision information.
- Record source-specific restrictions.
- Be prepared to release annotations and download scripts without redistributing images if necessary.

## Recommended paper design

Use a two-cohort benchmark.

### Cohort A: ScreenSpot-v2-variants

Purpose: realistic positive-versus-absent evaluation.

First annotation pilot:

- Select 75 screenshot groups.
- Stratify 25 each from desktop, mobile and web.
- Balance icon and text targets.
- Create one positive and one negative case per screenshot.
- Total: 150 cases.
- Keep paired cases together.
- Two independent annotators plus adjudication.

Confirmatory expansion:

- Select about 300 screenshot groups.
- One positive plus one human-verified negative per screenshot.
- Total: about 600 cases.
- Deduplicate screenshot and instruction families.
- Split by fine application family, never individual row.

### Cohort B: newly collected challenge cases

Purpose: target states absent from ScreenSpot-v2-variants.

Collect approximately 400–600 cases across at least 20 independently identified applications, emphasizing:

- Multiple plausible targets.
- Occlusion.
- Offscreen targets.
- Visually unclear targets.
- Hard unique controls matched to those cases.

### Combined target

The combined paper dataset should contain roughly 1,000–1,200 cases. ScreenSpot-v2-variants can provide about half of them, reducing original screenshot collection while preserving the study's full taxonomy.

## Required conversion

For each selected ScreenSpot row:

1. Create a positive case from `instruction` and `bbox`.
2. Create a paired candidate-absent case from `negative_instruction` with no box.
3. Assign a shared `screenshot_group_id`.
4. Preserve platform, source row ID, UI type, original filename and revision.
5. Resize once for Jev and transform the positive box exactly.
6. Hide the source positive/negative designation from annotators.
7. Collect two independent labels.
8. Adjudicate disagreement before freezing.

The original `action`, `decription`, `negative_action`, and `negative_description` fields may be retained for provenance but must not be shown to annotators or passed to Jev in the primary experiment.

## Bottom line

ScreenSpot-v2-variants materially improves the project. It supplies a large, public, cross-platform source of candidate absent instructions and matched positive controls. It does not remove the need for human review, finer application grouping, special-category data, license clarification, or a fresh confirmatory split.
