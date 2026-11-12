#!/bin/sh
# Run only saved-data analysis. Never invokes a collection script or API client.
set -eu
cd "$(dirname "$0")/.."
analysis_python="${JEV_ANALYSIS_PYTHON:-.venv/bin/python}"
document_python="${JEV_DOCUMENT_PYTHON:-$analysis_python}"
"$analysis_python" scripts/evaluate_external_confirmatory.py
"$analysis_python" scripts/extended_analysis.py
"$analysis_python" scripts/reviewer_analysis.py
"$analysis_python" scripts/evaluate_iteration3_collection.py
"$analysis_python" scripts/render_iteration3_comparison.py
"$analysis_python" scripts/render_paper_math.py
"$document_python" scripts/build_paper_pdf.py
"$analysis_python" -m pytest -q
