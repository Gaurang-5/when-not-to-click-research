#!/usr/bin/env python3
"""Download external images referenced by the academic manifest.

Images are fetched for local research use and are not bundled by the dataset
builder. With --prepare-jev, a second copy is resized to a maximum side of 1568
pixels; normalized boxes in the manifest remain valid after this resize.
"""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "academic_2000"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=("all", "screenspot", "imagejev"), default="all")
    p.add_argument("--prepare-jev", action="store_true")
    p.add_argument("--limit", type=int)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA,
                   help="Dataset directory containing manifest.jsonl")
    args = p.parse_args()
    data = args.data_dir.resolve()
    rows = [json.loads(x) for x in (data / "manifest.jsonl").read_text().splitlines() if x.strip()]
    wanted = {
        "screenspot": {"ScreenSpot-v2-variants"},
        "imagejev": {"ImageJevBench Box public v0.1"},
        "all": {"ScreenSpot-v2-variants", "ImageJevBench Box public v0.1"},
    }[args.source]
    unique = {}
    for row in rows:
        if row["source_dataset"] in wanted:
            unique[row["local_image_path"]] = row
    jobs = list(sorted(unique.values(), key=lambda r: r["local_image_path"]))
    if args.limit is not None:
        jobs = jobs[: args.limit]
    if args.workers < 1 or args.workers > 32:
        p.error("--workers must be between 1 and 32")

    def process(row):
        target = data / row["local_image_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = row.get("image_sha256")
        valid_existing = target.exists()
        if valid_existing and expected and sha256(target) != expected:
            target.unlink()
            valid_existing = False
        if not valid_existing:
            partial = target.with_name(target.name + ".part")
            if partial.exists():
                partial.unlink()
            req = urllib.request.Request(row["image_locator"], headers={"User-Agent": "jev-academic-dataset/1.0"})
            with urllib.request.urlopen(req, timeout=120) as src, partial.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            partial.replace(target)
        digest = sha256(target)
        if expected and digest != expected:
            raise ValueError(f"Checksum mismatch for {target}")
        try:
            with Image.open(target) as image:
                image.load()
                width, height = image.size
                prepared = ""
                if args.prepare_jev:
                    prepared_path = data / "images" / "jev_ready" / target.name
                    prepared_path.parent.mkdir(parents=True, exist_ok=True)
                    copy = image.convert("RGB") if image.mode not in ("RGB", "RGBA") else image.copy()
                    copy.thumbnail((1568, 1568), Image.Resampling.LANCZOS)
                    if prepared_path.suffix.lower() in (".jpg", ".jpeg") and copy.mode != "RGB":
                        copy = copy.convert("RGB")
                    save_kwargs = {"quality": 95} if prepared_path.suffix.lower() in (".jpg", ".jpeg") else {}
                    copy.save(prepared_path, **save_kwargs)
                    prepared = str(prepared_path.relative_to(data))
        except Exception:
            # A prior interrupted download may have left a corrupt non-hashed
            # ScreenSpot file. Remove it so a retry can recover cleanly.
            target.unlink(missing_ok=True)
            raise
        return {"local_image_path": row["local_image_path"], "sha256": digest,
                "width": width, "height": height, "jev_ready_path": prepared,
                "filename": target.name}

    log = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process, row): row for row in jobs}
        for index, future in enumerate(as_completed(futures), 1):
            item = future.result()
            log.append({k: item[k] for k in ("local_image_path", "sha256", "width", "height", "jev_ready_path")})
            print(f"[{index}/{len(jobs)}] {item['filename']}")
    log.sort(key=lambda item: item["local_image_path"])
    with (data / "materialized_images.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=("local_image_path", "sha256", "width", "height", "jev_ready_path"))
        w.writeheader(); w.writerows(log)


if __name__ == "__main__":
    main()
