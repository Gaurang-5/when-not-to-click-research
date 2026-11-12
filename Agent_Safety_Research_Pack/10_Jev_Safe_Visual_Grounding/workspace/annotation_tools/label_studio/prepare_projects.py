#!/usr/bin/env python3
"""Create two blind Label Studio task imports from the candidate manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "data" / "academic_2000" / "manifest.jsonl"
DEFAULT_OUT = Path(__file__).resolve().parent


def local_url(row: dict) -> str:
    path = row["local_image_path"]
    if row["source_dataset"] in {"ScreenSpot-v2-variants", "ImageJevBench Box public v0.1"}:
        path = f"data/academic_2000/{path}"
    return "/data/local-files/?d=" + path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--all", action="store_true", help="Include all rows rather than only required human reviews")
    args = p.parse_args()
    rows = [json.loads(line) for line in args.manifest.read_text().splitlines() if line.strip()]
    if not args.all:
        rows = [r for r in rows if r["human_review_required"]]
    tasks = [{"data": {
        "case_id": r["case_id"],
        "instruction": r["instruction"],
        "image": local_url(r),
        "expected_width": r["width"],
        "expected_height": r["height"],
    }} for r in rows]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, seed in (("annotator_a_tasks.json", 104729), ("annotator_b_tasks.json", 130363)):
        copy = list(tasks)
        random.Random(seed).shuffle(copy)
        (args.output_dir / name).write_text(json.dumps(copy, ensure_ascii=False, indent=2) + "\n")
    digest = hashlib.sha256("\n".join(sorted(t["data"]["case_id"] for t in tasks)).encode()).hexdigest()
    print(json.dumps({"annotators": 2, "tasks_per_annotator": len(tasks), "case_set_sha256": digest,
                      "output_dir": str(args.output_dir.resolve())}, indent=2))


if __name__ == "__main__":
    main()
