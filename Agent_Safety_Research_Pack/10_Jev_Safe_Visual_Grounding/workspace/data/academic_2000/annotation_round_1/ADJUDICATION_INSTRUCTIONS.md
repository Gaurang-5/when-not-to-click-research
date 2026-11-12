# Final adjudication instructions

Open **JEV Final Adjudication** in Label Studio. It contains 259 cases selected before viewing any Jev predictions.

For every case:

1. Read the instruction and inspect the clean screenshot.
2. Use the comparison image only to understand the two independent annotations: red is Annotator A and blue is Annotator B.
3. Choose exactly one final status: `unique`, `absent`, `multiple`, `occluded`, `offscreen`, or `unclear`.
4. For `unique`, draw exactly one tight rectangle around the full clickable element on the clean screenshot.
5. For `multiple`, draw every valid matching clickable element (at least two).
6. For every other status, draw no box.
7. Add a short note when overriding either annotator or when the case remains borderline.
8. Submit and proceed to the next case.

Do not view Jev outputs or model predictions during adjudication. Both authors should resolve difficult cases together and record the reason. When all 259 are complete, export the entire project as JSON. The freeze script will reject missing, extra, or structurally invalid decisions.

Run after export:

```bash
.venv/bin/python scripts/finalize_annotation_round.py \
  --adjudication-export /absolute/path/to/jev-final-adjudication-export.json
```
