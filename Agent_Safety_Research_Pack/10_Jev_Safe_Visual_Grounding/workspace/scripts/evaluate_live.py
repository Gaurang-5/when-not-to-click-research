"""Evaluate the held-out live Jev run using only the frozen policy."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.calibration import reliability
from src.metrics import correctness, risk_curve, summarize
from src.policies import decide, features, score
from src.statistical_tests import cluster_bootstrap, holm, paired_randomization
from src.validate_data import load, validate


class FrozenLogistic:
    def __init__(self, coef, intercept):
        self.coef = np.asarray(coef, dtype=float)[0]
        self.intercept = float(np.asarray(intercept, dtype=float)[0])

    def predict_proba(self, x):
        z = np.asarray(x, dtype=float) @ self.coef + self.intercept
        p = 1.0 / (1.0 + np.exp(-z))
        return np.column_stack([1.0 - p, p])


def latest_by_case(path):
    attempts, by_case = [], {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        attempts.append(record)
        previous = by_case.get(record['case_id'])
        if previous is None or record.get('status') == 'ok':
            by_case[record['case_id']] = record
    return attempts, by_case


def freeze_checked():
    path = ROOT / 'results/live_frozen_policy.json'
    digest_path = ROOT / 'results/live_frozen_policy.sha256'
    expected = digest_path.read_text().split()[0]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected != actual:
        raise SystemExit('Frozen policy hash mismatch')
    return json.loads(path.read_text()), actual


def threshold_value(value):
    return np.inf if value == 'Infinity' else float(value)


def plot_live(curves, rel, table, unique_ious, out):
    fig, ax = plt.subplots(figsize=(7, 4))
    for name in ['A', 'B', 'C', 'D', 'E']:
        pts = curves[name]
        ax.plot([p['coverage'] for p in pts], [p['risk'] for p in pts], marker='.', ms=3, label=name)
    ax.set(xlabel='Coverage (all held-out cases)', ylabel='Incorrect / accepted clicks',
           title='Live Jev 1.14 — descriptive risk vs coverage', xlim=(0, 1), ylim=(0, 1))
    ax.legend(); fig.tight_layout(); fig.savefig(out / 'live_risk_coverage.png', dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4)); ax.plot([0, 1], [0, 1], 'k--')
    for name in ['presence_all', 'box_event_all', 'joint_all']:
        bins = [b for b in rel[name]['bins'] if b['n']]
        ax.plot([b['confidence'] for b in bins], [b['frequency'] for b in bins], marker='o', label=name)
    ax.set(xlabel='Mean score in equal-width bin', ylabel='Observed event frequency',
           title='Live Jev 1.14 — held-out reliability')
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(out / 'live_reliability.png', dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    display = {'presence': 'Presence', 'uniqueness': 'Uniqueness',
               'presence_uniqueness': 'P+U'}
    names = [display.get(r['policy'], r['policy']) for r in table]
    ax.bar(names, [r['coverage'] for r in table], label='Coverage')
    ax.plot(names, [np.nan if r['selective_risk'] is None else r['selective_risk'] for r in table],
            'ro-', label='Selective risk')
    ax.set(title='Live Jev 1.14 — frozen policy comparison', ylim=(0, 1))
    ax.tick_params(axis='x', rotation=25); ax.legend(); fig.tight_layout()
    fig.savefig(out / 'live_policy_comparison.png', dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4)); ax.hist(unique_ious, bins=10, range=(0, 1))
    ax.set(title='Live Jev 1.14 — unique-target localization', xlabel='IoU', ylabel='Held-out unique cases')
    fig.tight_layout(); fig.savefig(out / 'live_localization.png', dpi=180); plt.close(fig)


def main():
    cases = load(ROOT / 'data/pilot_cases.jsonl')
    validate(cases, ROOT)
    freeze, freeze_sha = freeze_checked()
    attempts, by_case = latest_by_case(ROOT / 'results/live_calls.jsonl')

    if len(by_case) != len(cases) or set(by_case) != {r['case_id'] for r in cases}:
        raise SystemExit('Live collection is incomplete or contains unknown cases')
    if any((r.get('raw_response') or {}).get('model', r.get('model_version')) != 'jev-1.14.0' for r in attempts):
        raise SystemExit('Unexpected resolved model version')

    rows = [r for r in cases if r['split'] == 'test']
    preds = [by_case[r['case_id']] for r in rows]
    if len(rows) != 80 or len(preds) != 80:
        raise SystemExit('Expected exactly 80 held-out cases')

    joint = FrozenLogistic(freeze['joint_coef'], freeze['joint_intercept'])
    thresholds = {k: threshold_value(v) for k, v in freeze['thresholds'].items()}
    policies = ['A', 'B', 'C', 'D', 'E', 'presence', 'uniqueness', 'presence_uniqueness']
    correct, overlaps = correctness(rows, preds)
    table, strata, intervals, curves, accepted_by, actions_by = [], [], [], {}, {}, {}

    for policy in policies:
        scores = score(preds, policy, joint)
        accepted, actions = decide(preds, scores, thresholds[policy])
        accepted_by[policy], actions_by[policy] = accepted, actions
        metrics = {'policy': policy, 'threshold': thresholds[policy], **summarize(rows, preds, accepted, actions)}
        table.append(metrics)
        curves[policy] = risk_curve(rows, preds, scores)

        for group in ['target_status', 'template_id', 'layout_family', 'target_size', 'clutter', 'difficulty']:
            for value in sorted({r[group] for r in rows}):
                idx = [i for i, r in enumerate(rows) if r[group] == value]
                strata.append({'policy': policy, 'stratum': group, 'value': value,
                    **summarize([rows[i] for i in idx], [preds[i] for i in idx],
                                accepted[idx], [actions[i] for i in idx])})

        for metric in ['coverage', 'selective_risk', 'marginal_incorrect_action_rate',
                       'absent_false_accept_rate', 'ambiguous_wrong_accept_rate',
                       'unique_useful_automation_rate']:
            def statistic(idx, metric=metric):
                return summarize([rows[i] for i in idx], [preds[i] for i in idx],
                                 accepted[idx], [actions[i] for i in idx])[metric]
            intervals.append({'policy': policy, 'metric': metric,
                              **cluster_bootstrap(rows, statistic, n_boot=1000)})

    presence = np.array([p['presence_confidence'] if p['status'] == 'ok' else np.nan for p in preds])
    box = np.array([p['box_confidence'] if p['status'] == 'ok' else np.nan for p in preds])
    joint_score = joint.predict_proba(features(preds))[:, 1]
    joint_score[np.array([p['status'] != 'ok' for p in preds])] = np.nan
    visible = np.array([r['target_status'] not in ['absent', 'offscreen'] for r in rows])
    rel = {}
    for name, values, labels in [('presence', presence, visible), ('box_event', box, correct),
                                 ('joint', joint_score, correct)]:
        rel[name + '_all'] = reliability(values, labels)
        for category in ['absent', 'multiple', 'unique']:
            idx = np.array([r['target_status'] == category for r in rows])
            rel[name + '_' + category] = reliability(values[idx], labels[idx])

    comparisons = []
    for category in ['absent', 'multiple']:
        idx = [i for i, r in enumerate(rows) if r['target_status'] == category]
        subrows = [rows[i] for i in idx]
        difference = accepted_by['D'][idx].astype(int) - accepted_by['B'][idx].astype(int)
        comparisons.append({'endpoint': category, 'comparison': 'D_minus_B', 'n': len(idx),
            **paired_randomization(subrows, difference, n_perm=10000),
            'difference_ci': cluster_bootstrap(subrows, lambda ii: float(difference[ii].mean()), n_boot=1000)})
    adjusted = holm([c['p_cluster_sign'] for c in comparisons])
    for comparison, p in zip(comparisons, adjusted):
        comparison['p_holm'] = p

    by_policy = {r['policy']: r for r in table}
    d, b = by_policy['D'], by_policy['B']
    practical = {
        'absent_reduction_D_vs_B': b['absent_false_accept_rate'] - d['absent_false_accept_rate'],
        'ambiguous_reduction_D_vs_B': b['ambiguous_wrong_accept_rate'] - d['ambiguous_wrong_accept_rate'],
        'unique_useful_automation_change_D_vs_B': d['unique_useful_automation_rate'] - b['unique_useful_automation_rate'],
    }
    practical['criterion_met'] = bool(
        practical['absent_reduction_D_vs_B'] >= 0.10 and
        practical['ambiguous_reduction_D_vs_B'] >= 0.10 and
        practical['unique_useful_automation_change_D_vs_B'] >= -0.05
    )

    out = ROOT / 'results'
    pd.DataFrame(table).to_csv(out / 'live_policy_metrics.csv', index=False)
    pd.DataFrame(strata).to_csv(out / 'live_stratified_metrics.csv', index=False)
    pd.DataFrame(intervals).to_csv(out / 'live_confidence_intervals.csv', index=False)
    (out / 'live_calibration.json').write_text(json.dumps(rel, indent=2, allow_nan=False) + '\n')
    (out / 'live_comparisons.json').write_text(json.dumps(comparisons, indent=2, allow_nan=False) + '\n')
    (out / 'live_risk_curves.json').write_text(json.dumps(curves, indent=2, allow_nan=False) + '\n')

    errors = []
    for policy in policies:
        for i, row in enumerate(rows):
            if (accepted_by[policy][i] and not correct[i]) or (not accepted_by[policy][i] and correct[i]):
                errors.append({'case_id': row['case_id'], 'target_status': row['target_status'],
                    'layout_family': row['layout_family'], 'policy': policy,
                    'decision': actions_by[policy][i],
                    'incorrect_accept': bool(accepted_by[policy][i] and not correct[i]),
                    'missed_correct_automation': bool(not accepted_by[policy][i] and correct[i]),
                    'iou': float(overlaps[i])})
    pd.DataFrame(errors).to_csv(out / 'live_error_analysis.csv', index=False)

    test_attempts = [r for r in attempts if r['case_id'] in {x['case_id'] for x in rows}]
    all_usage = [(r.get('usage') or (r.get('raw_response') or {}).get('usage') or {}) for r in attempts]
    test_usage = [(r.get('usage') or (r.get('raw_response') or {}).get('usage') or {}) for r in test_attempts]
    total_input = sum(u.get('input_tokens', 0) for u in all_usage)
    test_input = sum(u.get('input_tokens', 0) for u in test_usage)
    summary = {
        'provenance': 'real Jev API responses', 'model': 'jev-1.14.0',
        'frozen_policy_sha256': freeze_sha, 'test_cases': len(rows),
        'test_outputs_ok': sum(p['status'] == 'ok' for p in preds),
        'test_outputs_failed': sum(p['status'] != 'ok' for p in preds),
        'all_network_attempts': len(attempts), 'all_successful_outputs': sum(r['status'] == 'ok' for r in attempts),
        'all_failed_outputs': sum(r['status'] != 'ok' for r in attempts),
        'total_input_tokens': total_input, 'total_output_tokens': sum(u.get('output_tokens', 0) for u in all_usage),
        'total_estimated_cost_usd': total_input * 0.042 / 1_000_000,
        'test_input_tokens': test_input, 'test_output_tokens': sum(u.get('output_tokens', 0) for u in test_usage),
        'test_estimated_cost_usd': test_input * 0.042 / 1_000_000,
        'test_mean_latency_ms': float(np.mean([r['latency_ms'] for r in test_attempts])),
        'test_median_latency_ms': float(np.median([r['latency_ms'] for r in test_attempts])),
        'test_p95_latency_ms': float(np.percentile([r['latency_ms'] for r in test_attempts], 95)),
        'practical_criterion': practical,
        'policy_metrics': by_policy,
        'primary_comparisons': comparisons,
        'limitations': ['procedural labels without independent human review',
                        'synthetic interfaces from one generator', 'only two held-out layout families',
                        'template bootstrap does not capture family-level uncertainty']
    }
    encoded = json.dumps(summary, indent=2, allow_nan=False) + '\n'
    (out / 'live_execution_summary.json').write_text(encoded)
    (out / 'live_execution_summary.sha256').write_text(
        hashlib.sha256(encoded.encode()).hexdigest() + '  live_execution_summary.json\n')
    plot_live(curves, rel, table, overlaps[np.array([r['target_status'] == 'unique' for r in rows])], out)

    print(json.dumps({'state': 'EVALUATED', 'test_cases': len(rows), 'test_ok': summary['test_outputs_ok'],
        'total_cost_usd': summary['total_estimated_cost_usd'], 'practical_criterion_met': practical['criterion_met']}))
    print(pd.DataFrame(table)[['policy', 'accepted', 'coverage', 'selective_risk',
        'marginal_incorrect_action_rate', 'absent_false_accept_rate',
        'ambiguous_wrong_accept_rate', 'unique_useful_automation_rate']].to_string(index=False))


if __name__ == '__main__':
    main()
