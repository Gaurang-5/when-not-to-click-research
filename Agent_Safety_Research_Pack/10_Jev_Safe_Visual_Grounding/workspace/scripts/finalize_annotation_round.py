#!/usr/bin/env python3
"""Merge two independent annotations with a complete adjudication export."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from analyze_label_studio_exports import LOCALIZABLE, iou, parse_export


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "data" / "academic_2000" / "annotation_round_1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def match_and_average(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    if len(a) != len(b) or not a:
        raise ValueError("Boxes must be non-empty and have equal counts")
    order = max(
        itertools.permutations(range(len(b))),
        key=lambda candidate: sum(iou(a[i], b[j]) for i, j in enumerate(candidate)),
    )
    return [[round((x + y) / 2, 3) for x, y in zip(a[i], b[j])] for i, j in enumerate(order)]


def parse_adjudication(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    parsed: dict[str, dict] = {}
    for task in raw:
        case_id = task.get("data", {}).get("case_id")
        active = [a for a in task.get("annotations", []) if not a.get("was_cancelled")]
        if not case_id or len(active) != 1:
            raise ValueError(f"Invalid adjudication record for {case_id!r}: active_annotations={len(active)}")
        statuses, boxes, notes = [], [], []
        width = int(task["data"].get("expected_width") or 0)
        height = int(task["data"].get("expected_height") or 0)
        for result in active[0].get("result", []):
            value = result.get("value", {})
            if result.get("from_name") == "adjudicated_status":
                statuses.extend(value.get("choices", []))
            elif result.get("from_name") == "adjudicated_boxes":
                boxes.append([
                    round(value["x"] * width / 100, 3),
                    round(value["y"] * height / 100, 3),
                    round((value["x"] + value["width"]) * width / 100, 3),
                    round((value["y"] + value["height"]) * height / 100, 3),
                ])
            elif result.get("from_name") == "adjudication_notes":
                notes.extend(value.get("text", []))
        if len(statuses) != 1:
            raise ValueError(f"{case_id}: expected one adjudicated status, found {statuses}")
        status = statuses[0]
        if status == "unique" and len(boxes) != 1:
            raise ValueError(f"{case_id}: unique requires exactly one final box")
        if status == "multiple" and len(boxes) < 2:
            raise ValueError(f"{case_id}: multiple requires at least two final boxes")
        if status not in LOCALIZABLE and boxes:
            raise ValueError(f"{case_id}: {status} requires zero final boxes")
        parsed[case_id] = {"status": status, "boxes_xyxy": boxes, "notes": " | ".join(notes)}
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", type=Path, default=ROUND / "corrected_exports" / "annotator_a_corrected.json")
    parser.add_argument("--annotator-b", type=Path, default=ROUND / "corrected_exports" / "annotator_b_corrected.json")
    parser.add_argument("--comparison", type=Path, default=ROUND / "corrected_analysis" / "case_comparison.csv")
    parser.add_argument("--adjudication-export", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROUND / "frozen_labels")
    parser.add_argument("--adjudication-provenance", default="author_adjudication")
    parser.add_argument("--adjudication-rule", default="Flagged cases use blinded author adjudication; unflagged localizable boxes use the coordinate-wise mean after maximum-IoU matching.")
    args = parser.parse_args()

    a, ia = parse_export(args.annotator_a, "A")
    b, ib = parse_export(args.annotator_b, "B")
    if ia or ib:
        raise SystemExit(f"Independent exports still contain format errors: A={len(ia)}, B={len(ib)}")
    with args.comparison.open(encoding="utf-8") as handle:
        comparison = {row["case_id"]: row for row in csv.DictReader(handle)}
    required = {case_id for case_id, row in comparison.items() if row["review_required"].lower() == "true"}
    adjudicated = parse_adjudication(args.adjudication_export)
    if set(adjudicated) != required:
        raise SystemExit(
            f"Adjudication set mismatch: required={len(required)}, exported={len(adjudicated)}, "
            f"missing={len(required-set(adjudicated))}, extra={len(set(adjudicated)-required)}"
        )

    final = []
    for case_id in sorted(a):
        aa, bb = a[case_id], b[case_id]
        if case_id in adjudicated:
            decision = adjudicated[case_id]
            status, boxes = decision["status"], decision["boxes_xyxy"]
            provenance = args.adjudication_provenance
            notes = decision["notes"]
        else:
            if aa["status"] != bb["status"]:
                raise AssertionError(f"Unreviewed status disagreement: {case_id}")
            status = aa["status"]
            boxes = match_and_average(aa["boxes_xyxy"], bb["boxes_xyxy"]) if status in LOCALIZABLE else []
            provenance = "two_annotator_consensus"
            notes = ""
        final.append({
            "case_id": case_id,
            "instruction": aa["instruction"],
            "image": aa["image"],
            "width": aa["width"],
            "height": aa["height"],
            "target_status": status,
            "boxes_xyxy": boxes,
            "label_provenance": provenance,
            "adjudication_notes": notes,
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    jsonl = args.output_dir / "final_labels.jsonl"
    jsonl.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in final), encoding="utf-8")
    with (args.output_dir / "final_labels.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["case_id", "instruction", "image", "width", "height", "target_status", "boxes_xyxy", "label_provenance", "adjudication_notes"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in final:
            out = dict(row)
            out["boxes_xyxy"] = json.dumps(out["boxes_xyxy"])
            writer.writerow(out)
    manifest = {
        "state": "FROZEN",
        "cases": len(final),
        "status_counts": dict(Counter(row["target_status"] for row in final)),
        "consensus_cases": sum(row["label_provenance"] == "two_annotator_consensus" for row in final),
        "adjudicated_cases": sum(row["case_id"] in adjudicated for row in final),
        "annotator_a_sha256": sha256(args.annotator_a),
        "annotator_b_sha256": sha256(args.annotator_b),
        "adjudication_export_sha256": sha256(args.adjudication_export),
        "final_labels_sha256": sha256(jsonl),
        "rule": args.adjudication_rule,
    }
    (args.output_dir / "freeze_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "CHECKSUMS.sha256").write_text(
        f"{sha256(jsonl)}  final_labels.jsonl\n{sha256(args.output_dir / 'final_labels.csv')}  final_labels.csv\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
