#!/usr/bin/env python3
"""Build two separate, self-contained Label Studio annotator ZIP files."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABEL_DIR = ROOT / "annotation_tools" / "label_studio"
HANDOFFS = ROOT.parent / "handoffs"

ANNOTATORS = {
    "A": LABEL_DIR / "annotator_a_tasks.json",
    "B": LABEL_DIR / "annotator_b_tasks.json",
}


CHEAT_SHEET = """# Annotation cheat sheet

For every task, read the instruction and inspect only what is visible in the screenshot.

1. Choose exactly one status:
   - `unique`: exactly one valid visible target; draw one box.
   - `multiple`: two or more equally valid visible targets; box every valid target.
   - `absent`: no valid target is visible; draw no box.
   - `occluded`: the intended target is visibly blocked; draw no box and add a note.
   - `offscreen`: evidence shows the target requires scrolling or navigation; draw no box and add a note.
   - `unclear`: the instruction or target cannot be resolved reliably; draw no box and add a note.
2. For `unique` or `multiple`, click `valid_target` and drag a tight box around the complete clickable area.
3. Select `high`, `medium`, or `low` confidence.
4. Use low confidence and a note instead of guessing.
5. Press Submit before moving to the next task.

Do not use case-ID suffixes as hints. Do not use AI or consult another annotator.
"""


IMAGE_HELP = """# Image troubleshooting

If an image does not appear:

1. Confirm that this ZIP was fully extracted.
2. Restart Label Studio using the included launcher.
3. Open **Settings -> Cloud Storage -> Add Source Storage -> Local Files**.
4. Set the absolute path to the `data` folder inside this extracted package.
5. Save and synchronize the storage, then reload the task.

Do not rename or move files inside `data`.
"""


MAC_LAUNCHER = """#!/bin/zsh
set -e
package_dir="$(cd "$(dirname "$0")" && pwd)"
cd "$package_dir"
export LOCAL_FILES_SERVING_ENABLED=true
export LOCAL_FILES_DOCUMENT_ROOT="$package_dir"
if command -v label-studio >/dev/null 2>&1; then
  exec label-studio start --port 8080
fi
if [[ -x "$HOME/.local/bin/label-studio" ]]; then
  exec "$HOME/.local/bin/label-studio" start --port 8080
fi
echo "Label Studio was not found in this Terminal environment."
echo "Activate the environment where it is installed, then run this file again."
read -r "?Press Return to close."
"""


WINDOWS_LAUNCHER = r"""@echo off
cd /d "%~dp0"
set LOCAL_FILES_SERVING_ENABLED=true
set LOCAL_FILES_DOCUMENT_ROOT=%CD%
label-studio start --port 8080
if errorlevel 1 (
  echo Label Studio was not found. Activate the Python environment where it is installed and run this file again.
  pause
)
"""


def readme(letter: str) -> str:
    lower = letter.lower()
    return f"""# JEV Annotator {letter} package

This is the private package for **Annotator {letter}**. It contains all 951 study cases. The other annotators receive the same cases in different orders.

## Rules

- Work independently and do not discuss real study cases.
- Do not view another annotator's project or export.
- Do not use AI, Jev predictions, source labels, or case-ID suffixes as hints.
- Use low confidence and a note instead of guessing.

## Setup

1. Fully extract this ZIP. Do not work inside the ZIP preview.
2. Start Label Studio with `START_LABEL_STUDIO_MAC.command` on macOS or `START_LABEL_STUDIO_WINDOWS.bat` on Windows.
3. Open `http://localhost:8080`.
4. Create a project named **JEV Annotation {letter}**.
5. Import `assigned_tasks.json`.
6. Open **Settings -> Labeling Interface -> Custom template**.
7. Paste the complete contents of `config.xml` and save.
8. Open one task and confirm that the screenshot loads. If not, follow `IMAGE_TROUBLESHOOTING.md`.

Read `ANNOTATION_CHEAT_SHEET.md` and `ANNOTATOR_INSTRUCTIONS.md` before production labeling. Update `PROGRESS_TRACKER.csv` daily.

## Export

After submitting all 951 tasks, choose **Export -> JSON** and save the untouched file as:

```text
annotator_{lower}_export.json
```

Return only that raw JSON export to Gaurang. Do not export COCO, YOLO, or CSV.
"""


def copy_or_link(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_one(letter: str, task_file: Path, expected_case_set: set[str] | None):
    package_name = f"JEV_ANNOTATOR_{letter}_PACKAGE"
    package = HANDOFFS / package_name
    archive = HANDOFFS / f"{package_name}.zip"

    if package.exists():
        shutil.rmtree(package)
    for path in (archive,):
        if path.exists():
            path.unlink()
    package.mkdir(parents=True)

    tasks = json.loads(task_file.read_text())
    case_set = {task["data"]["case_id"] for task in tasks}
    if len(case_set) != len(tasks):
        raise RuntimeError(f"Annotator {letter} has duplicate case IDs")
    if expected_case_set is not None and case_set != expected_case_set:
        raise RuntimeError(f"Annotator {letter} case set differs")

    image_paths = {
        task["data"]["image"].split("?d=", 1)[-1] for task in tasks
    }
    missing = []
    for relative in sorted(image_paths):
        source = ROOT / relative
        if not source.is_file():
            missing.append(relative)
        else:
            copy_or_link(source, package / relative)
    if missing:
        raise RuntimeError(f"Annotator {letter} is missing {len(missing)} images")

    shutil.copy2(task_file, package / "assigned_tasks.json")
    shutil.copy2(LABEL_DIR / "config.xml", package / "config.xml")
    shutil.copy2(
        LABEL_DIR / "ANNOTATOR_INSTRUCTIONS.md",
        package / "ANNOTATOR_INSTRUCTIONS.md",
    )
    (package / "README_FIRST.md").write_text(readme(letter))
    (package / "ANNOTATION_CHEAT_SHEET.md").write_text(CHEAT_SHEET)
    (package / "IMAGE_TROUBLESHOOTING.md").write_text(IMAGE_HELP)
    (package / "START_LABEL_STUDIO_MAC.command").write_text(MAC_LAUNCHER)
    (package / "START_LABEL_STUDIO_WINDOWS.bat").write_text(WINDOWS_LAUNCHER)
    (package / "START_LABEL_STUDIO_MAC.command").chmod(
        (package / "START_LABEL_STUDIO_MAC.command").stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )
    (package / "PROGRESS_TRACKER.csv").write_text(
        "annotator,date,completed_total,remaining,technical_problem\n"
        f"Annotator {letter},,0,{len(tasks)},\n"
    )
    manifest = {
        "annotator": letter,
        "tasks": len(tasks),
        "unique_images": len(image_paths),
        "missing_images": 0,
        "export_filename": f"annotator_{letter.lower()}_export.json",
    }
    (package / "PACKAGE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as zf:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                zf.write(path, Path(package_name) / path.relative_to(package))
    digest = sha256_file(archive)
    return case_set, {**manifest, "archive": str(archive), "sha256": digest}


def main() -> None:
    HANDOFFS.mkdir(parents=True, exist_ok=True)
    expected = None
    results = []
    for letter, task_file in ANNOTATORS.items():
        expected, result = build_one(letter, task_file, expected)
        results.append(result)
    print(json.dumps({"packages": results, "identical_case_sets": True}, indent=2))


if __name__ == "__main__":
    main()
