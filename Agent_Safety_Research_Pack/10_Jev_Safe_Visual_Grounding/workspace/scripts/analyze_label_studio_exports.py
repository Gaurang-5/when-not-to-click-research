#!/usr/bin/env python3
"""Validate two Label Studio exports and build agreement/adjudication artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "academic_2000"
LABELS = {"unique", "absent", "multiple", "occluded", "offscreen", "unclear"}
LOCALIZABLE = {"unique", "multiple"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box_percent_to_px(result: dict, width: int, height: int) -> list[float]:
    value = result["value"]
    x1 = value["x"] * width / 100
    y1 = value["y"] * height / 100
    x2 = (value["x"] + value["width"]) * width / 100
    y2 = (value["y"] + value["height"]) * height / 100
    return [round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)]


def parse_export(path: Path, annotator: str) -> tuple[dict[str, dict], list[dict]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a JSON list")
    parsed: dict[str, dict] = {}
    issues: list[dict] = []
    for task in raw:
        data = task.get("data", {})
        case_id = data.get("case_id")
        if not case_id:
            issues.append({"annotator": annotator, "case_id": "", "issue": "missing_case_id"})
            continue
        if case_id in parsed:
            issues.append({"annotator": annotator, "case_id": case_id, "issue": "duplicate_case_id"})
            continue
        annotations = [a for a in task.get("annotations", []) if not a.get("was_cancelled")]
        if len(annotations) != 1:
            issues.append({"annotator": annotator, "case_id": case_id, "issue": f"active_annotations={len(annotations)}"})
        results = annotations[-1].get("result", []) if annotations else []
        statuses: list[str] = []
        confidences: list[str] = []
        notes: list[str] = []
        box_results: list[dict] = []
        for result in results:
            name = result.get("from_name")
            if name == "target_status":
                statuses.extend(result.get("value", {}).get("choices", []))
            elif name == "confidence":
                confidences.extend(result.get("value", {}).get("choices", []))
            elif name == "notes":
                notes.extend(result.get("value", {}).get("text", []))
            elif name == "target_boxes":
                box_results.append(result)
        if len(statuses) != 1 or statuses[0] not in LABELS:
            issues.append({"annotator": annotator, "case_id": case_id, "issue": f"invalid_status={statuses}"})
        if len(confidences) != 1 or confidences[0] not in {"high", "medium", "low"}:
            issues.append({"annotator": annotator, "case_id": case_id, "issue": f"invalid_confidence={confidences}"})
        status = statuses[0] if len(statuses) == 1 else None
        confidence = confidences[0] if len(confidences) == 1 else None
        width = int(data.get("expected_width") or 0)
        height = int(data.get("expected_height") or 0)
        boxes = []
        for result in box_results:
            try:
                box = box_percent_to_px(result, width, height)
                if not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height):
                    raise ValueError("outside image")
                boxes.append(box)
            except Exception as exc:
                issues.append({"annotator": annotator, "case_id": case_id, "issue": f"invalid_box={exc}"})
        if status == "unique" and len(boxes) != 1:
            issues.append({"annotator": annotator, "case_id": case_id, "issue": f"unique_requires_1_box_found_{len(boxes)}"})
        elif status == "multiple" and len(boxes) < 2:
            issues.append({"annotator": annotator, "case_id": case_id, "issue": f"multiple_requires_2plus_boxes_found_{len(boxes)}"})
        elif status not in LOCALIZABLE and boxes:
            issues.append({"annotator": annotator, "case_id": case_id, "issue": f"{status}_requires_0_boxes_found_{len(boxes)}"})
        parsed[case_id] = {
            "case_id": case_id,
            "instruction": data.get("instruction", ""),
            "image": data.get("image", ""),
            "width": width,
            "height": height,
            "status": status,
            "confidence": confidence,
            "boxes_xyxy": boxes,
            "notes": " | ".join(n.strip() for n in notes if n.strip()),
        }
    return parsed, issues


def iou(a: list[float], b: list[float]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union else 0.0


def matched_mean_iou(a: list[list[float]], b: list[list[float]]) -> float | None:
    if not a or len(a) != len(b):
        return None
    if len(a) <= 7:
        return max(sum(iou(a[i], b[j]) for i, j in enumerate(order)) / len(a)
                   for order in itertools.permutations(range(len(b))))
    remaining = set(range(len(b)))
    scores = []
    for box in a:
        best = max(remaining, key=lambda j: iou(box, b[j]))
        scores.append(iou(box, b[best]))
        remaining.remove(best)
    return sum(scores) / len(scores)


def cohens_kappa(a: list[str], b: list[str]) -> float | None:
    if not a:
        return None
    po = sum(x == y for x, y in zip(a, b)) / len(a)
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[label] / len(a)) * (cb[label] / len(b)) for label in LABELS)
    return (po - pe) / (1 - pe) if pe < 1 else None


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", type=Path, required=True)
    parser.add_argument("--annotator-b", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DATA / "annotation_round_1")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw_exports"
    raw_dir.mkdir(exist_ok=True)
    for source, name in ((args.annotator_a, "annotator_a_export.json"), (args.annotator_b, "annotator_b_export.json")):
        shutil.copy2(source, raw_dir / name)

    a, issues_a = parse_export(args.annotator_a, "A")
    b, issues_b = parse_export(args.annotator_b, "B")
    if set(a) != set(b):
        raise SystemExit(f"Case-set mismatch: A-only={len(set(a)-set(b))}, B-only={len(set(b)-set(a))}")
    case_ids = sorted(a)
    issue_rows = sorted(issues_a + issues_b, key=lambda r: (r["annotator"], r["case_id"], r["issue"]))
    issue_cases = {(r["annotator"], r["case_id"]) for r in issue_rows}

    manifest = {json.loads(line)["case_id"]: json.loads(line)
                for line in (DATA / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    comparison_rows = []
    adjudication_tasks = []
    status_pairs = Counter()
    box_ious = []
    for case_id in case_ids:
        aa, bb = a[case_id], b[case_id]
        status_agree = aa["status"] == bb["status"]
        status_pairs[(aa["status"], bb["status"])] += 1
        count_agree = len(aa["boxes_xyxy"]) == len(bb["boxes_xyxy"])
        mean_iou = matched_mean_iou(aa["boxes_xyxy"], bb["boxes_xyxy"]) if status_agree and aa["status"] in LOCALIZABLE else None
        if mean_iou is not None:
            box_ious.append(mean_iou)
        reasons = []
        if not status_agree:
            reasons.append("status_disagreement")
        if status_agree and aa["status"] in LOCALIZABLE and not count_agree:
            reasons.append("box_count_disagreement")
        if mean_iou is not None and mean_iou < 0.5:
            reasons.append("box_iou_below_0.5")
        if ("A", case_id) in issue_cases or ("B", case_id) in issue_cases:
            reasons.append("annotation_format_error")
        if aa["confidence"] == "low" or bb["confidence"] == "low":
            reasons.append("low_confidence")
        row = {
            "case_id": case_id,
            "instruction": aa["instruction"],
            "source_dataset": manifest.get(case_id, {}).get("source_dataset", ""),
            "proposed_split": manifest.get(case_id, {}).get("split", ""),
            "annotator_a_status": aa["status"],
            "annotator_b_status": bb["status"],
            "status_agree": status_agree,
            "annotator_a_confidence": aa["confidence"],
            "annotator_b_confidence": bb["confidence"],
            "annotator_a_box_count": len(aa["boxes_xyxy"]),
            "annotator_b_box_count": len(bb["boxes_xyxy"]),
            "matched_mean_iou": "" if mean_iou is None else round(mean_iou, 6),
            "annotator_a_boxes_xyxy": json.dumps(aa["boxes_xyxy"]),
            "annotator_b_boxes_xyxy": json.dumps(bb["boxes_xyxy"]),
            "annotator_a_notes": aa["notes"],
            "annotator_b_notes": bb["notes"],
            "review_reasons": ";".join(reasons),
            "review_required": bool(reasons),
        }
        comparison_rows.append(row)
        if reasons:
            adjudication_tasks.append({"data": {
                "case_id": case_id,
                "instruction": aa["instruction"],
                "image": aa["image"],
                "review_reasons": "; ".join(reasons),
                "annotator_a_summary": f"status={aa['status']}; confidence={aa['confidence']}; boxes={aa['boxes_xyxy']}; notes={aa['notes'] or '(none)'}",
                "annotator_b_summary": f"status={bb['status']}; confidence={bb['confidence']}; boxes={bb['boxes_xyxy']}; notes={bb['notes'] or '(none)'}",
            }})

    a_status = [a[c]["status"] for c in case_ids]
    b_status = [b[c]["status"] for c in case_ids]
    agreements = sum(x == y for x, y in zip(a_status, b_status))
    report = {
        "state": "PRELIMINARY_REQUIRES_CORRECTIONS" if issue_rows else "READY_FOR_ADJUDICATION",
        "tasks_per_annotator": len(case_ids),
        "case_sets_identical": True,
        "annotator_a_export_sha256": sha256(args.annotator_a),
        "annotator_b_export_sha256": sha256(args.annotator_b),
        "annotator_a_status_counts": Counter(a_status),
        "annotator_b_status_counts": Counter(b_status),
        "exact_status_agreements": agreements,
        "status_disagreements": len(case_ids) - agreements,
        "raw_status_agreement": agreements / len(case_ids),
        "cohens_kappa": cohens_kappa(a_status, b_status),
        "annotation_format_issues": len(issue_rows),
        "cases_flagged_for_review": sum(bool(r["review_required"]) for r in comparison_rows),
        "same_status_localizable_cases_with_comparable_boxes": len(box_ious),
        "mean_matched_box_iou": sum(box_ious) / len(box_ious) if box_ious else None,
        "status_pair_counts": {f"{x}__{y}": n for (x, y), n in sorted(status_pairs.items())},
    }
    (args.output_dir / "agreement_report.json").write_text(json.dumps(report, indent=2, default=dict) + "\n", encoding="utf-8")
    write_csv(args.output_dir / "validation_issues.csv", issue_rows, ["annotator", "case_id", "issue"])
    for annotator in ("A", "B"):
        write_csv(
            args.output_dir / f"corrections_annotator_{annotator.lower()}.csv",
            [row for row in issue_rows if row["annotator"] == annotator],
            ["annotator", "case_id", "issue"],
        )
    write_csv(args.output_dir / "case_comparison.csv", comparison_rows, list(comparison_rows[0]))
    (args.output_dir / "adjudication_tasks.json").write_text(json.dumps(adjudication_tasks, indent=2) + "\n", encoding="utf-8")
    reason_counts = Counter(
        reason
        for row in comparison_rows
        for reason in row["review_reasons"].split(";")
        if reason
    )
    report_title = (
        "Preliminary two-annotator agreement report"
        if issue_rows
        else "Two-annotator agreement report: ready for adjudication"
    )
    report_intro = (
        f"This report is preliminary because {len(issue_rows)} annotation-format errors must be corrected before final analysis."
        if issue_rows
        else "All annotation-format checks pass. The remaining flagged cases are ready for human adjudication."
    )
    report_md = f"""# {report_title}

{report_intro}

## Completeness

- Annotator A: {len(a)} unique cases
- Annotator B: {len(b)} unique cases
- Case sets: identical
- Missing cases: 0

## Preliminary agreement

- Exact status agreement: {agreements}/{len(case_ids)} ({agreements / len(case_ids):.1%})
- Status disagreements: {len(case_ids) - agreements}
- Cohen's kappa: {report['cohens_kappa']:.3f}
- Comparable same-status localization cases: {len(box_ious)}
- Mean matched box IoU: {report['mean_matched_box_iou']:.3f}

## Required work

- Correct format errors: {len(issue_rows)}
- Cases flagged for adjudication/review: {report['cases_flagged_for_review']}
- Status disagreements: {reason_counts['status_disagreement']}
- Same-status box IoU below 0.5: {reason_counts['box_iou_below_0.5']}
- Same-status box-count disagreements: {reason_counts['box_count_disagreement']}
- Cases with at least one low-confidence annotation: {reason_counts['low_confidence']}

Preserve both original exports. After the format errors are corrected, export the complete projects again and rerun the analysis. The authors may adjudicate the locked disagreements jointly; they must record the final status, boxes, and reason without consulting model predictions.
"""
    (args.output_dir / "PRELIMINARY_AGREEMENT_REPORT.md").write_text(report_md, encoding="utf-8")
    manifest_out = {
        "generated_files": ["agreement_report.json", "PRELIMINARY_AGREEMENT_REPORT.md", "validation_issues.csv", "corrections_annotator_a.csv", "corrections_annotator_b.csv", "case_comparison.csv", "adjudication_tasks.json"],
        "raw_exports": ["raw_exports/annotator_a_export.json", "raw_exports/annotator_b_export.json"],
        "warning": "Do not freeze labels until validation issues are corrected and every flagged case is adjudicated.",
    }
    (args.output_dir / "README.json").write_text(json.dumps(manifest_out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=dict))


if __name__ == "__main__":
    main()
