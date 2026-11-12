# Preliminary two-annotator agreement report

This report is preliminary because 13 annotation-format errors must be corrected before final analysis.

## Completeness

- Annotator A: 951 unique cases
- Annotator B: 951 unique cases
- Case sets: identical
- Missing cases: 0

## Preliminary agreement

- Exact status agreement: 755/951 (79.4%)
- Status disagreements: 196
- Cohen's kappa: 0.605
- Comparable same-status localization cases: 201
- Mean matched box IoU: 0.619

## Required work

- Correct format errors: 13
- Cases flagged for adjudication/review: 262
- Status disagreements: 196
- Same-status box IoU below 0.5: 44
- Same-status box-count disagreements: 5
- Cases with at least one low-confidence annotation: 36

Preserve both original exports. After the format errors are corrected, export the complete projects again and rerun the analysis. The authors may adjudicate the locked disagreements jointly; they must record the final status, boxes, and reason without consulting model predictions.
