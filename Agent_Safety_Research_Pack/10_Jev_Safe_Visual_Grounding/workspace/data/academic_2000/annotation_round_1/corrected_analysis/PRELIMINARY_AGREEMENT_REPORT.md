# Two-annotator agreement report: ready for adjudication

All annotation-format checks pass. The remaining flagged cases are ready for human adjudication.

## Completeness

- Annotator A: 951 unique cases
- Annotator B: 951 unique cases
- Case sets: identical
- Missing cases: 0

## Preliminary agreement

- Exact status agreement: 759/951 (79.8%)
- Status disagreements: 192
- Cohen's kappa: 0.613
- Comparable same-status localization cases: 205
- Mean matched box IoU: 0.619

## Required work

- Correct format errors: 0
- Cases flagged for adjudication/review: 259
- Status disagreements: 192
- Same-status box IoU below 0.5: 45
- Same-status box-count disagreements: 4
- Cases with at least one low-confidence annotation: 36

Preserve both original exports. After the format errors are corrected, export the complete projects again and rerun the analysis. The authors may adjudicate the locked disagreements jointly; they must record the final status, boxes, and reason without consulting model predictions.
