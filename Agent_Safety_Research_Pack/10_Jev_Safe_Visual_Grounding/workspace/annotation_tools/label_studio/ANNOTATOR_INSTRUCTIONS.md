# GUI Grounding Annotation Instructions

## Your task

For each screenshot, read the instruction and judge only what is visible in that screenshot. Choose exactly one status. Do not search the application, infer from hidden menus, or use an AI model.

## Status definitions

### `unique`

Exactly one visible and usable interface element correctly satisfies the instruction. Draw exactly one box around the complete clickable or tappable area.

### `absent`

No visible interface element correctly satisfies the instruction. Draw no box. A semantically related control is not sufficient.

### `multiple`

Two or more visible elements are equally valid matches and the instruction does not distinguish among them. Draw one box around every valid match.

### `occluded`

The intended element can be identified, but another visible layer such as a dialog, menu, tooltip, or overlay blocks the usable target. Draw no actionable target box and explain the obstruction in Notes.

### `offscreen`

The task explicitly establishes that the intended target lies outside the current viewport or requires scrolling/navigation before it can be seen. Draw no box and explain the evidence in Notes. If there is no such evidence, use `absent`.

### `unclear`

The instruction is ambiguous, corrupted, or cannot be resolved reliably from the screenshot. Draw no box and explain the ambiguity in Notes.

## Bounding-box rules

1. Draw boxes only for `unique` and `multiple`.
2. Enclose the entire clickable control, including its button background or row hit area. Do not box only the text glyph or icon when the containing button is visibly clickable.
3. Keep the box tight. Exclude shadows, neighboring controls, tooltips and unrelated padding.
4. For a text link without a visible container, enclose the complete rendered link text.
5. For `multiple`, draw every equally valid visible target.
6. Never draw a guessed box for an absent or hidden target.

## Independence rules

- Do not discuss cases with the other annotator.
- Do not view the other annotator’s project or export.
- Do not view Jev or baseline predictions.
- Do not use the source dataset’s existing label as a hint.
- Mark confidence `low` and leave a note instead of guessing.

## Examples

- Instruction “close this window,” with one visible X button: `unique`; box the whole close-button hit area.
- Instruction “save,” with no save control visible: `absent`; no box.
- Instruction “open Settings,” with two indistinguishable Settings buttons: `multiple`; box both.
- Instruction “click Submit,” but a modal covers Submit: `occluded`; no actionable box and note that the modal blocks it.
- Instruction “click the thing”: `unclear`; no box and explain that the target is unspecified.

Press **Submit** only after selecting one status and confidence level, and after checking the required number of boxes.
