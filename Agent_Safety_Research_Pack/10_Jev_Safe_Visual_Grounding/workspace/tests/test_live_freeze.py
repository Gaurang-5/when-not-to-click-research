import json
import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_live_freeze_is_real_and_does_not_use_test():
    path = ROOT / 'results/live_frozen_policy.json'
    expected = (ROOT / 'results/live_frozen_policy.sha256').read_text().split()[0]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    frozen = json.loads(path.read_text())
    assert frozen['provenance'] == 'real Jev API responses'
    assert frozen['test_used_for_selection'] is False
    assert frozen['collection']['dev_cases'] == 80
    assert frozen['collection']['calibration_cases'] == 40
    assert frozen['collection']['network_attempts'] == 120
    assert frozen['collection']['failed_outputs'] == 1
    assert frozen['joint_fit_n'] == 79
    assert set(frozen['thresholds']) == {
        'A', 'B', 'C', 'D', 'E', 'presence', 'uniqueness', 'presence_uniqueness'
    }


def test_test_collection_dry_run_requires_valid_freeze():
    completed = subprocess.run(
        [sys.executable, str(ROOT / 'scripts/run_pilot.py'), '--split', 'test', '--limit', '80'],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(completed.stdout)
    assert summary['state'] == 'NOT_RUN'
    assert summary['split'] == 'test'
    assert summary['selected_cases'] == 80
    assert summary['already_successful'] == 80
    assert summary['planned_calls'] == 0


def test_refreeze_is_rejected_after_test_collection():
    completed = subprocess.run(
        [sys.executable, str(ROOT / 'scripts/freeze_live_policy.py')],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode != 0
    assert 'Refusing to freeze after final-test responses exist' in completed.stderr
