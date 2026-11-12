#!/usr/bin/env python3
"""Merge completed independent reviews into a new, immutable manifest."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "academic_2000"
LABELS = {"unique", "absent", "multiple", "occluded", "offscreen", "unclear"}


def parse_boxes(value: str) -> list[list[float]]:
    if not value.strip():
        return []
    boxes = json.loads(value)
    if not isinstance(boxes, list):
        raise ValueError("boxes must be a JSON list")
    for box in boxes:
        if not isinstance(box, list) or len(box) != 4 or not all(isinstance(v, (int, float)) for v in box):
            raise ValueError("each box must be [x1,y1,x2,y2]")
        if not box[0] < box[2] or not box[1] < box[3]:
            raise ValueError("box edges are not ordered")
    return boxes


def normalize(boxes: list[list[float]], width: int, height: int) -> list[list[float]]:
    return [[round(b[0] / width, 8), round(b[1] / height, 8),
             round(b[2] / width, 8), round(b[3] / height, 8)] for b in boxes]


def main() -> None:
    manifest = [json.loads(x) for x in (DATA / "manifest.jsonl").read_text().splitlines() if x.strip()]
    with (DATA / "human_review_queue.csv").open(newline="", encoding="utf-8") as f:
        reviews = list(csv.DictReader(f))
    with (DATA / "published_label_audit_sample_150.csv").open(newline="", encoding="utf-8") as f:
        audit = list(csv.DictReader(f))

    incomplete = [r["case_id"] for r in reviews if r["review_status"].strip().lower() != "complete"]
    if incomplete:
        raise SystemExit(f"Refusing to finalize: {len(incomplete)} human reviews are incomplete")
    missing_audit = [r["case_id"] for r in audit if not r["audit_decision"].strip()]
    if missing_audit:
        raise SystemExit(f"Refusing to finalize: {len(missing_audit)} published-label audits are incomplete")
    disagreements = [r for r in audit if r["audit_decision"].strip().lower() not in {"agree", "pass", "correct"}]
    if len(disagreements) / len(audit) > 0.05:
        raise SystemExit("Published-label audit disagreement exceeds 5%; audit all source positives before finalizing")

    review_by_id = {r["case_id"]: r for r in reviews}
    for row in manifest:
        review = review_by_id.get(row["case_id"])
        if review is None:
            row["split_locked"] = True
            continue
        a1, a2 = review["annotator_1_label"].strip(), review["annotator_2_label"].strip()
        if a1 not in LABELS or a2 not in LABELS:
            raise SystemExit(f"Invalid or missing annotator label for {row['case_id']}")
        if a1 == a2:
            label = a1
            b1, b2 = parse_boxes(review["annotator_1_boxes_xyxy"]), parse_boxes(review["annotator_2_boxes_xyxy"])
            if b1 != b2 and label in {"unique", "multiple"}:
                raise SystemExit(f"Box disagreement for {row['case_id']} requires adjudication")
            boxes = b1
        else:
            label = review["adjudicated_label"].strip()
            if label not in LABELS:
                raise SystemExit(f"Label disagreement for {row['case_id']} requires adjudication")
            boxes = parse_boxes(review["adjudicated_boxes_xyxy"])
        if label == "unique" and len(boxes) != 1:
            raise SystemExit(f"Unique case {row['case_id']} must have exactly one box")
        if label == "multiple" and len(boxes) < 2:
            raise SystemExit(f"Multiple case {row['case_id']} must have at least two boxes")
        if label not in {"unique", "multiple", "offscreen"} and boxes:
            raise SystemExit(f"Non-localizable case {row['case_id']} must not have boxes")
        row["target_status"] = label
        row["ground_truth_boxes_px"] = boxes
        row["ground_truth_boxes_norm"] = normalize(boxes, row["width"], row["height"])
        row["reference_action"] = "click" if label == "unique" else "clarify" if label in {"multiple", "unclear"} else "abstain"
        row["localization_eligibility"] = label == "unique"
        row["label_status"] = "independent_two_annotator_review_complete"
        row["human_review_required"] = False
        row["split_locked"] = True

    out = DATA / "manifest_reviewed.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in manifest), encoding="utf-8")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    (DATA / "manifest_reviewed.sha256").write_text(f"{digest}  manifest_reviewed.jsonl\n", encoding="utf-8")
    print(json.dumps({"state": "FINALIZED", "rows": len(manifest), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
