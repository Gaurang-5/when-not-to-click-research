"""Fit and freeze live Jev policies without loading final-test predictions.

Development fits the logistic baseline. Calibration chooses operating thresholds.
Malformed or failed calls remain in metric denominators and always fail closed.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.calibration import coverage_threshold, fit_joint
from src.metrics import correctness, summarize
from src.policies import decide, score, valid_box
from src.validate_data import load, validate


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latest_by_case(path):
    records = []
    by_case = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        records.append(record)
        # A later successful explicit retry supersedes an earlier failed attempt for
        # prediction, while all attempts remain in the operational totals below.
        current = by_case.get(record['case_id'])
        if current is None or record.get('status') == 'ok':
            by_case[record['case_id']] = record
    return records, by_case


def safe_prediction(case_id, by_case):
    return by_case.get(case_id, {
        'case_id': case_id,
        'status': 'missing',
        'presence_confidence': None,
        'uniqueness_confidence': None,
        'box_confidence': None,
        'predicted_box': None,
    })


def metrics_for(rows, preds, policies, thresholds, joint):
    output = {}
    for policy in policies:
        scores = score(preds, policy, joint)
        accepted, actions = decide(preds, scores, thresholds[policy])
        output[policy] = summarize(rows, preds, accepted, actions)
    return output


def main():
    log_path = ROOT / 'results/live_calls.jsonl'
    if not log_path.exists():
        raise SystemExit('No live call log found')

    config_path = ROOT / 'configs/experiment.json'
    cases_path = ROOT / 'data/pilot_cases.jsonl'
    cases = load(cases_path)
    validate(cases, ROOT)
    attempts, by_case = latest_by_case(log_path)

    # Guard the final test: this program refuses to consume or overwrite a freeze
    # if any test response already exists.
    split_for = {row['case_id']: row['split'] for row in cases}
    test_records = [r for r in attempts if split_for.get(r.get('case_id')) == 'test']
    if test_records:
        raise SystemExit('Refusing to freeze after final-test responses exist')

    split = {}
    for name in ('dev', 'calibration'):
        rows = [row for row in cases if row['split'] == name]
        preds = [safe_prediction(row['case_id'], by_case) for row in rows]
        split[name] = (rows, preds)

    dev_rows, dev_preds = split['dev']
    cal_rows, cal_preds = split['calibration']
    missing = {
        name: [p['case_id'] for p in preds if p.get('status') == 'missing']
        for name, (_, preds) in split.items()
    }
    if missing['dev'] or missing['calibration']:
        raise SystemExit(f'Incomplete collection: {missing}')

    # Schema failures cannot supply features for fitting. They remain failed,
    # fail-closed observations in every reported metric.
    dev_correct, _ = correctness(dev_rows, dev_preds)
    fit_indices = [
        i for i, p in enumerate(dev_preds)
        if p.get('status') == 'ok' and valid_box(p)
        and all(p.get(k) is not None for k in (
            'presence_confidence', 'uniqueness_confidence', 'box_confidence'))
    ]
    if len(set(bool(dev_correct[i]) for i in fit_indices)) < 2:
        raise SystemExit('Development fit needs both correct and incorrect examples')
    joint = fit_joint(
        [dev_preds[i] for i in fit_indices],
        dev_correct[fit_indices],
    )

    policies = ['A', 'B', 'C', 'D', 'E', 'presence', 'uniqueness', 'presence_uniqueness']
    target_coverage = json.loads(config_path.read_text())['target_calibration_coverage']
    thresholds = {}
    for policy in policies:
        thresholds[policy] = (
            0.0 if policy == 'A'
            else coverage_threshold(score(cal_preds, policy, joint), target_coverage)
        )

    dev_metrics = metrics_for(dev_rows, dev_preds, policies, thresholds, joint)
    cal_metrics = metrics_for(cal_rows, cal_preds, policies, thresholds, joint)

    relevant_attempts = [
        r for r in attempts if split_for.get(r.get('case_id')) in {'dev', 'calibration'}
    ]
    input_tokens = sum((r.get('usage') or {}).get('input_tokens', 0) for r in relevant_attempts)
    output_tokens = sum((r.get('usage') or {}).get('output_tokens', 0) for r in relevant_attempts)
    operational = {
        'network_attempts': len(relevant_attempts),
        'successful_outputs': sum(r.get('status') == 'ok' for r in relevant_attempts),
        'failed_outputs': sum(r.get('status') != 'ok' for r in relevant_attempts),
        'failure_reasons': dict(Counter(
            r.get('error_message', 'unknown') for r in relevant_attempts
            if r.get('status') != 'ok'
        )),
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'estimated_cost_usd': input_tokens * 0.042 / 1_000_000,
        'mean_latency_ms': float(np.mean([r['latency_ms'] for r in relevant_attempts])),
        'median_latency_ms': float(np.median([r['latency_ms'] for r in relevant_attempts])),
        'p95_latency_ms': float(np.percentile([r['latency_ms'] for r in relevant_attempts], 95)),
    }

    freeze = {
        'provenance': 'real Jev API responses',
        'model': 'jev-1.14.0',
        'prompt_version': 'presence-count-box-v1',
        'created_after_splits': ['dev', 'calibration'],
        'test_used_for_selection': False,
        'target_calibration_coverage': target_coverage,
        'threshold_rule': 'highest attainable calibration coverage <= target; ties use larger threshold',
        'failed_call_rule': 'fail closed; retain in denominators; do not impute scores',
        'joint_fit_rule': 'regularized logistic regression on valid development outputs only',
        'joint_fit_n': len(fit_indices),
        'thresholds': {
            key: value if np.isfinite(value) else 'Infinity'
            for key, value in thresholds.items()
        },
        'joint_features': ['presence_confidence', 'uniqueness_confidence', 'box_confidence'],
        'joint_coef': joint.coef_.tolist(),
        'joint_intercept': joint.intercept_.tolist(),
        'hashes': {
            'experiment_config_sha256': sha256(config_path),
            'case_manifest_sha256': sha256(cases_path),
            'jev_client_sha256': sha256(ROOT / 'src/jev_client.py'),
            'parser_sha256': sha256(ROOT / 'src/parse_outputs.py'),
            'policies_sha256': sha256(ROOT / 'src/policies.py'),
            'metrics_sha256': sha256(ROOT / 'src/metrics.py'),
            'freeze_script_sha256': sha256(Path(__file__)),
        },
        'collection': {
            'dev_cases': len(dev_rows),
            'calibration_cases': len(cal_rows),
            **operational,
        },
        'development_metrics_at_frozen_thresholds': dev_metrics,
        'calibration_metrics_at_frozen_thresholds': cal_metrics,
    }
    encoded = json.dumps(freeze, indent=2, allow_nan=False) + '\n'
    out = ROOT / 'results/live_frozen_policy.json'
    out.write_text(encoded)
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    (ROOT / 'results/live_frozen_policy.sha256').write_text(f'{digest}  live_frozen_policy.json\n')

    print(json.dumps({
        'state': 'FROZEN',
        'output': str(out),
        'sha256': digest,
        'dev_cases': len(dev_rows),
        'calibration_cases': len(cal_rows),
        'test_responses_seen': 0,
        'failed_outputs': operational['failed_outputs'],
        'estimated_cost_usd': operational['estimated_cost_usd'],
    }))


if __name__ == '__main__':
    main()
