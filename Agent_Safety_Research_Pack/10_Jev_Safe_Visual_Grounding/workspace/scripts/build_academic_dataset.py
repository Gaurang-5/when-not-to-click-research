#!/usr/bin/env python3
"""Build the versioned 2,000-task academic candidate dataset.

The builder intentionally separates published/procedural labels from labels that
still require independent human verification.  It does not download or
redistribute third-party screenshots.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "academic_2000"
SNAPSHOTS = DEFAULT_OUT / "source_snapshots"
VARIANTS_REV = "aa4d83b6833d77d3bb3b7cb769951e2db80052b6"
IMAGEJEV_REV = "609a664e81f46e03731600bd7bd9f1b7a61257c5"
GUI_RECOVER_REV = "5878d5ac7dae36362788cc4f795dde5e4b4bba4d"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm_box(box: list[float], width: int, height: int) -> list[float]:
    x1, y1, x2, y2 = box
    return [round(x1 / width, 8), round(y1 / height, 8), round(x2 / width, 8), round(y2 / height, 8)]


def stable_split(group_id: str) -> str:
    # Image-linked pairs always receive the same proposal. The split is not
    # locked until human validation and leakage checks are complete.
    bucket = int(hashlib.sha256(group_id.encode()).hexdigest()[:8], 16) % 100
    if bucket < 20:
        return "development"
    if bucket < 40:
        return "calibration"
    return "test"


def select_screen_rows(rows: list[dict[str, Any]], count: int = 750) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda r: (r["platform"], r["img_filename"], r["id"]))
    first_by_image: dict[str, dict[str, Any]] = {}
    extras: list[dict[str, Any]] = []
    for row in ordered:
        if row["img_filename"] not in first_by_image:
            first_by_image[row["img_filename"]] = row
        else:
            extras.append(row)
    selected = list(first_by_image.values())
    extras.sort(key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())
    selected.extend(extras[: count - len(selected)])
    if len(selected) != count:
        raise ValueError(f"Expected {count} ScreenSpot rows, got {len(selected)}")
    return sorted(selected, key=lambda r: r["id"])


def screen_case(row: dict[str, Any], negative: bool) -> dict[str, Any]:
    width, height = map(int, row["img_size"])
    source_id = row["id"]
    role = "absent_candidate" if negative else "positive"
    case_id = f"ssv2v_{source_id}_{'neg' if negative else 'pos'}"
    pair_id = f"ssv2v_{source_id}_{'pos' if negative else 'neg'}"
    image = row["img_filename"]
    image_url = (
        "https://huggingface.co/datasets/likaixin/ScreenSpot-v2-variants/resolve/"
        f"{VARIANTS_REV}/images/{quote(image)}"
    )
    original_box = [float(v) for v in row["bbox"]]
    clipped_box = [
        max(0.0, min(original_box[0], width)),
        max(0.0, min(original_box[1], height)),
        max(0.0, min(original_box[2], width)),
        max(0.0, min(original_box[3], height)),
    ]
    geometry_adjusted = clipped_box != original_box
    boxes_px = [] if negative else [clipped_box]
    boxes_norm = [] if negative else [norm_box(boxes_px[0], width, height)]
    return {
        "dataset_row_version": "1.0",
        "case_id": case_id,
        "task_kind": "gui_grounding",
        "source_dataset": "ScreenSpot-v2-variants",
        "source_revision": VARIANTS_REV,
        "source_item_id": source_id,
        "source_url": "https://huggingface.co/datasets/likaixin/ScreenSpot-v2-variants",
        "image_locator": image_url,
        "local_image_path": f"images/external/screenspot_v2_variants/{image}",
        "instruction": row["negative_instruction"] if negative else row["instruction"],
        "instruction_role": role,
        "target_status": "absent_candidate" if negative else "unique",
        "label_status": "needs_two_annotator_verification" if negative or geometry_adjusted else "source_published",
        "human_review_required": negative or geometry_adjusted,
        "width": width,
        "height": height,
        "bbox_format": "xyxy_absolute_and_normalized",
        "ground_truth_boxes_px": boxes_px,
        "ground_truth_boxes_norm": boxes_norm,
        "reference_action": "abstain" if negative else "click",
        "localization_eligibility": not negative,
        "element_type": row.get("ui_type") or "unknown",
        "interface_source": row.get("application") or row.get("platform") or "unknown",
        "platform": row.get("platform") or "unknown",
        "application": row.get("application") or "unknown",
        "layout_family": "real_gui",
        "difficulty": "unrated",
        "source_license": "Apache-2.0 claimed by parent ScreenSpot-v2",
        "license_status": "parent_license_claim_requires_release_review",
        "redistribution_status": "manifest_only; fetch from source repository",
        "provenance_note": (
            "Negative instruction is a source-provided candidate and is not treated as verified absent until two-person review."
            if negative else
            "Source-published positive annotation; one out-of-bounds edge was clipped and the row was added to human review."
            if geometry_adjusted else
            "Source-published positive annotation."
        ),
        "geometry_qc": "source_box_clipped_to_image_bounds" if geometry_adjusted and not negative else "pass",
        "ground_truth_box_original_px": original_box if geometry_adjusted and not negative else None,
        "image_group_id": f"screenspot:{image}",
        "proposed_split": stable_split(f"screenspot:{image}"),
        "split_locked": False,
        "paired_case_id": pair_id,
    }


def imagejev_case(row: dict[str, Any]) -> dict[str, Any]:
    width, height = int(row["width"]), int(row["height"])
    g = row["gold"]
    box_norm = [float(g["left"]), float(g["top"]), float(g["right"]), float(g["bottom"])]
    box_px = [round(box_norm[0] * width, 4), round(box_norm[1] * height, 4),
              round(box_norm[2] * width, 4), round(box_norm[3] * height, 4)]
    image = row["image"]
    family = row["family"]
    element_type = {"ui": "ui_element", "doc": "document_field", "coco": "visual_object"}.get(family, family)
    return {
        "dataset_row_version": "1.0",
        "case_id": f"imagejev_{row['id']}",
        "task_kind": "visual_grounding",
        "source_dataset": "ImageJevBench Box public v0.1",
        "source_revision": IMAGEJEV_REV,
        "source_item_id": row["id"],
        "source_url": "https://github.com/fstandhartinger/jevbench/tree/main/datasets/imagejev-box-v0.1",
        "image_locator": f"https://raw.githubusercontent.com/fstandhartinger/jevbench/{IMAGEJEV_REV}/datasets/imagejev-box-v0.1/{image}",
        "local_image_path": f"images/external/imagejev_box_v0_1/{Path(image).name}",
        "instruction": row["instructions"],
        "instruction_role": "positive",
        "target_status": "unique",
        "label_status": "source_published_second_annotator_qc",
        "human_review_required": False,
        "width": width,
        "height": height,
        "bbox_format": "xyxy_absolute_and_normalized",
        "ground_truth_boxes_px": [box_px],
        "ground_truth_boxes_norm": [box_norm],
        "reference_action": "click",
        "localization_eligibility": True,
        "element_type": element_type,
        "interface_source": family,
        "platform": "image" if family == "coco" else family,
        "application": family,
        "layout_family": row["kind"],
        "difficulty": row.get("size_bucket") or "unrated",
        "source_license": row["license"],
        "license_status": "per_item_license_and_attribution_available",
        "redistribution_status": "manifest_only; preserve per-item license and attribution",
        "provenance_note": row["attribution"],
        "image_sha256": row["sha256"],
        "image_group_id": f"imagejev:{row['id']}",
        "proposed_split": "test_external",
        "split_locked": True,
        "paired_case_id": None,
    }


def synthetic_case(row: dict[str, Any]) -> dict[str, Any]:
    boxes_px = [[float(v) for v in box] for box in row["ground_truth_boxes"]]
    boxes_norm = [norm_box(box, int(row["width"]), int(row["height"])) for box in boxes_px]
    return {
        "dataset_row_version": "1.0",
        "case_id": f"synthetic_{row['case_id']}",
        "task_kind": "gui_grounding",
        "source_dataset": "Jev safe GUI grounding synthetic pilot",
        "source_revision": "local_pilot_v1",
        "source_item_id": row["case_id"],
        "source_url": "local",
        "image_locator": row["screenshot_path"],
        "local_image_path": row["screenshot_path"],
        "instruction": row["instruction"],
        "instruction_role": "positive" if row["target_status"] != "absent" else "absent",
        "target_status": row["target_status"],
        "label_status": "procedural_needs_independent_human_review",
        "human_review_required": True,
        "width": int(row["width"]),
        "height": int(row["height"]),
        "bbox_format": "xyxy_absolute_and_normalized",
        "ground_truth_boxes_px": boxes_px,
        "ground_truth_boxes_norm": boxes_norm,
        "reference_action": row["reference_action"],
        "localization_eligibility": bool(row["localization_eligibility"]),
        "element_type": "synthetic_ui_element",
        "interface_source": "authored_html",
        "platform": "web_synthetic",
        "application": row["application_id"],
        "layout_family": row["layout_family"],
        "difficulty": row["difficulty"],
        "source_license": row["source_license"],
        "license_status": "project_authored",
        "redistribution_status": "included locally",
        "provenance_note": "Procedurally generated label; independent human review is required before publication claims.",
        "image_sha256": row["screenshot_sha256"],
        "image_group_id": f"synthetic:{row['template_id']}",
        "proposed_split": "development" if row["split"] == "dev" else row["split"],
        "split_locked": True,
        "paired_case_id": None,
    }


def counterfactual_rows(samples: list[dict[str, Any]], annotations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {s["sample_id"]: s for s in samples}
    out: list[dict[str, Any]] = []
    for ann in annotations:
        sample = by_id[ann["sample_id"]]
        candidates = {int(c["id"]): c for c in sample["candidates"]}
        width, height = map(int, sample["image_size"])
        for neg in ann["negatives"]:
            c = candidates[int(neg["candidate_id"])]
            out.append({
                "sample_id": ann["sample_id"],
                "source_revision": GUI_RECOVER_REV,
                "instruction": sample["instruction"],
                "image_reference": Path(sample["img"]).name,
                "width": width,
                "height": height,
                "gt_box_xyxy": sample["gt_box"],
                "gt_box_norm": norm_box(sample["gt_box"], width, height),
                "candidate_id": int(neg["candidate_id"]),
                "candidate_box_xyxy": c["box"],
                "candidate_box_norm": norm_box(c["box"], width, height),
                "candidate_text": c.get("text", ""),
                "candidate_source": c.get("source", ""),
                "error_type": neg["error_type"],
                "difficulty": neg["difficulty"],
                "rationale": neg["rationale"],
                "label_status": "pilot_candidate_human_spot_checked_not_benchmark_ground_truth",
                "source_license": "CC-BY-4.0 annotations; upstream image terms apply",
            })
    return out


def flatten(row: dict[str, Any]) -> dict[str, Any]:
    return {k: json.dumps(v, ensure_ascii=False, separators=(",", ":")) if isinstance(v, (list, dict)) else v for k, v in row.items()}


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flatten(r) for r in rows)


def write_checksums(out_dir: Path) -> None:
    files = [p for p in out_dir.rglob("*") if p.is_file() and p.name != "CHECKSUMS.sha256"]
    lines = []
    for path in sorted(files):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(out_dir)}")
    (out_dir / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    screen_rows: list[dict[str, Any]] = []
    for platform in ("desktop", "mobile", "web"):
        screen_rows.extend(read_json(SNAPSHOTS / f"screenspot_variants_{platform}.json"))
    selected = select_screen_rows(screen_rows)
    primary: list[dict[str, Any]] = []
    for row in selected:
        primary.extend((screen_case(row, False), screen_case(row, True)))

    imagejev = read_jsonl(SNAPSHOTS / "imagejev_items.jsonl")
    if len(imagejev) != 300:
        raise ValueError(f"Expected 300 ImageJev items, got {len(imagejev)}")
    primary.extend(imagejev_case(row) for row in imagejev)

    synthetic = read_jsonl(ROOT / "data" / "pilot_cases.jsonl")
    if len(synthetic) != 200:
        raise ValueError(f"Expected 200 local pilot cases, got {len(synthetic)}")
    primary.extend(synthetic_case(row) for row in synthetic)
    if len(primary) != 2000 or len({r['case_id'] for r in primary}) != 2000:
        raise ValueError("Primary manifest must contain exactly 2,000 unique cases")

    cf = counterfactual_rows(
        read_json(SNAPSHOTS / "gui_recover_samples.json"),
        read_json(SNAPSHOTS / "gui_recover_annotations.json"),
    )
    if len(cf) != 66:
        raise ValueError(f"Expected 66 GUI-Recover candidates, got {len(cf)}")

    (out / "manifest.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in primary), encoding="utf-8"
    )
    write_csv(out / "manifest.csv", primary)
    write_csv(out / "counterfactual_candidates.csv", cf)

    review = [r for r in primary if r["human_review_required"]]
    review_rows = [{
        "case_id": r["case_id"], "image_group_id": r["image_group_id"],
        "image_locator": r["image_locator"], "instruction": r["instruction"],
        "width": r["width"], "height": r["height"],
        "current_label": r["target_status"],
        "current_boxes_xyxy": r["ground_truth_boxes_px"],
        "annotator_1_label": "", "annotator_1_boxes_xyxy": "", "annotator_1_notes": "",
        "annotator_2_label": "", "annotator_2_boxes_xyxy": "", "annotator_2_notes": "",
        "adjudicated_label": "", "adjudicated_boxes_xyxy": "", "adjudicator_notes": "",
        "review_status": "pending",
    } for r in review]
    write_csv(out / "human_review_queue.csv", review_rows)

    published = [r for r in primary if not r["human_review_required"]]
    published.sort(key=lambda r: hashlib.sha256(r["case_id"].encode()).hexdigest())
    audit = published[:150]
    write_csv(out / "published_label_audit_sample_150.csv", [{
        "case_id": r["case_id"], "source_dataset": r["source_dataset"],
        "image_locator": r["image_locator"], "instruction": r["instruction"],
        "source_label": r["target_status"], "audit_decision": "", "audit_notes": "",
    } for r in audit])

    source_counts = Counter(r["source_dataset"] for r in primary)
    label_counts = Counter(r["target_status"] for r in primary)
    split_counts = Counter(r["proposed_split"] for r in primary)
    report = {
        "dataset_name": "Jev Safe Visual Grounding Academic Candidate 2000",
        "version": "1.0-candidate",
        "primary_task_count": len(primary),
        "unique_image_groups": len({r["image_group_id"] for r in primary}),
        "source_counts": dict(source_counts),
        "target_status_counts": dict(label_counts),
        "proposed_split_counts": dict(split_counts),
        "human_review_required": len(review),
        "published_label_audit_sample": len(audit),
        "auxiliary_counterfactual_candidates": len(cf),
        "external_images_included": False,
        "release_state": "candidate_manifest_not_publication_ready_until_review_queue_is_complete",
    }
    (out / "BUILD_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_checksums(out)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
