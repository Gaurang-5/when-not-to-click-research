import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_external_evaluator_writes_json_with_failed_outputs(tmp_path):
    """Regression: NumPy failure counts must not make summary JSON fail."""
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/evaluate_external_confirmatory.py"),
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["failed_outputs"] == 11
    assert summary["failure_reasons"] == {
        "degenerate/reversed box": 6,
        "Choice probabilities do not sum to one": 5,
    }
    absent = summary["primary_comparisons"][0]
    assert absent["case_weighted_difference"] == -0.0125
    assert absent["cluster_weighted_difference"] == -0.011146496815286623
    assert summary["operations"]["auth_rejected_attempts"] == 71
    assert summary["operations"]["billable_http_200_attempts"] == 951
    assert summary["operations"]["input_tokens"] == 3199297
    assert summary["operations"]["output_tokens"] == 73284
    assert summary["operations"]["estimated_cost_usd"] == 0.134370474
