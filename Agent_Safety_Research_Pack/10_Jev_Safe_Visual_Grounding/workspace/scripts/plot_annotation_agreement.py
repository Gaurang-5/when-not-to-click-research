#!/usr/bin/env python3
"""Generate publication figures for the two-annotator labeling round."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "academic_2000" / "annotation_round_1" / "corrected_analysis"
OUT = ROOT / "results" / "human_annotation"
LABELS = ["unique", "absent", "multiple", "occluded", "offscreen", "unclear"]


def main() -> None:
    report = json.loads((ANALYSIS / "agreement_report.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    matrix = np.zeros((len(LABELS), len(LABELS)), dtype=int)
    for key, count in report["status_pair_counts"].items():
        a, b = key.split("__")
        matrix[LABELS.index(a), LABELS.index(b)] = count
    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    image = ax.imshow(matrix, cmap="Blues")
    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            color = "white" if matrix[i, j] > matrix.max() * 0.45 else "#111827"
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color=color, fontsize=10)
    ax.set_xticks(range(len(LABELS)), LABELS, rotation=35, ha="right")
    ax.set_yticks(range(len(LABELS)), LABELS)
    ax.set_xlabel("Annotator B")
    ax.set_ylabel("Annotator A")
    ax.set_title("Independent target-status annotations (n=951)")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Cases")
    fig.tight_layout()
    fig.savefig(OUT / "status_confusion_matrix.png", dpi=220)
    fig.savefig(OUT / "status_confusion_matrix.pdf")
    plt.close(fig)

    metrics = [
        ("Exact status\nagreement", report["raw_status_agreement"]),
        ("Cohen's\nkappa", report["cohens_kappa"]),
        ("Mean matched\nbox IoU", report["mean_matched_box_iou"]),
    ]
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    bars = ax.bar([m[0] for m in metrics], [m[1] for m in metrics], color=["#2563EB", "#7C3AED", "#059669"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title("Pre-adjudication annotation quality")
    ax.grid(axis="y", alpha=0.25)
    for bar, (_, value) in zip(bars, metrics):
        ax.text(bar.get_x() + bar.get_width()/2, value + 0.025, f"{value:.3f}", ha="center", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "agreement_summary.png", dpi=220)
    fig.savefig(OUT / "agreement_summary.pdf")
    plt.close(fig)
    print(json.dumps({"state": "GENERATED", "output": str(OUT), "files": 4}))


if __name__ == "__main__":
    main()
