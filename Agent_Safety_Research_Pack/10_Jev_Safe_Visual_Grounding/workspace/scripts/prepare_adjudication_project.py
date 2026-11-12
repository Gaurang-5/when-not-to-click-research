#!/usr/bin/env python3
"""Create visual comparison previews and Label Studio tasks for adjudication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image, ImageDraw, ImageFont

from analyze_label_studio_exports import parse_export


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "data" / "academic_2000" / "annotation_round_1"


def local_path(image_url: str) -> Path:
    parsed = urlparse(image_url)
    relative = parse_qs(parsed.query).get("d", [""])[0]
    if not relative:
        raise ValueError(f"Unsupported Label Studio image URL: {image_url}")
    return ROOT / relative


def draw_box(draw: ImageDraw.ImageDraw, box: list[float], colour: str, label: str, width: int) -> None:
    x1, y1, x2, y2 = box
    line = max(3, round(min(width, 1600) / 300))
    draw.rectangle((x1, y1, x2, y2), outline=colour, width=line)
    text_y = max(0, y1 - 22)
    draw.rectangle((x1, text_y, x1 + 26, text_y + 20), fill=colour)
    draw.text((x1 + 6, text_y + 2), label, fill="white")


def build_preview(source: Path, destination: Path, a: dict, b: dict) -> None:
    with Image.open(source) as raw:
        image = raw.convert("RGB")
    draw = ImageDraw.Draw(image)
    for box in a["boxes_xyxy"]:
        draw_box(draw, box, "#D62728", "A", image.width)
    for box in b["boxes_xyxy"]:
        draw_box(draw, box, "#1F77B4", "B", image.width)

    font = ImageFont.load_default()
    legend = (
        f"A (red): {a['status']} / {a['confidence']} / {len(a['boxes_xyxy'])} box(es)    "
        f"B (blue): {b['status']} / {b['confidence']} / {len(b['boxes_xyxy'])} box(es)"
    )
    bbox = draw.textbbox((0, 0), legend, font=font)
    pad = 8
    draw.rectangle((0, 0, min(image.width, bbox[2] + pad * 2), bbox[3] + pad * 2), fill="#111827")
    draw.text((pad, pad), legend, fill="white", font=font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", type=Path, default=ROUND / "corrected_exports" / "annotator_a_corrected.json")
    parser.add_argument("--annotator-b", type=Path, default=ROUND / "corrected_exports" / "annotator_b_corrected.json")
    parser.add_argument("--review-tasks", type=Path, default=ROUND / "corrected_analysis" / "adjudication_tasks.json")
    parser.add_argument("--preview-dir", type=Path, default=ROUND / "adjudication_previews")
    parser.add_argument("--output", type=Path, default=ROUND / "adjudication_project_tasks.json")
    args = parser.parse_args()

    a, issues_a = parse_export(args.annotator_a, "A")
    b, issues_b = parse_export(args.annotator_b, "B")
    if issues_a or issues_b:
        raise SystemExit(f"Correct annotation format errors first: A={len(issues_a)}, B={len(issues_b)}")
    review = json.loads(args.review_tasks.read_text(encoding="utf-8"))
    output = []
    for item in review:
        data = dict(item["data"])
        case_id = data["case_id"]
        if case_id not in a or case_id not in b:
            raise KeyError(case_id)
        source = local_path(data["image"])
        if not source.is_file():
            raise FileNotFoundError(source)
        preview = args.preview_dir / f"{case_id}.png"
        build_preview(source, preview, a[case_id], b[case_id])
        preview_relative = preview.relative_to(ROOT).as_posix()
        data["comparison_image"] = f"/data/local-files/?d={preview_relative}"
        data["expected_width"] = a[case_id]["width"]
        data["expected_height"] = a[case_id]["height"]
        output.append({"data": data})

    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"state": "READY_TO_IMPORT", "tasks": len(output), "previews": str(args.preview_dir), "output": str(args.output)}))


if __name__ == "__main__":
    main()
