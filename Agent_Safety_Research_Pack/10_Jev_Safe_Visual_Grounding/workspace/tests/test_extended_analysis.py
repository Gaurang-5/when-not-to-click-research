"""Regression checks for the scientific provenance corrections and ratio edge cases."""
import json
from pathlib import Path
import numpy as np
from scripts.extended_analysis import bootstrap,load
ROOT=Path(__file__).resolve().parents[1]

def test_bootstrap_does_not_report_zero_risk_for_zero_accepts():
    rows=[{'source_image':'a','target_status':'unique'},{'source_image':'b','target_status':'absent'}]
    out=bootstrap(rows,np.array([True,False]),np.array([False,False]),n_boot=30)
    assert out['coverage']['low']==out['coverage']['high']==0
    assert out['selective_risk']['low'] is None
    assert out['selective_risk']['defined_replicates']==0

def test_bootstrap_keeps_shared_screenshot_as_one_unit():
    rows=[{'source_image':'same','target_status':'unique'},{'source_image':'same','target_status':'absent'}]
    out=bootstrap(rows,np.array([True,False]),np.array([True,True]),n_boot=30)
    assert out['selective_risk']['low']==out['selective_risk']['high']==.5
    assert out['coverage']['low']==1

def test_external_labels_are_partitioned_by_source_not_assumed_independent():
    rows,_=load()
    real=[r for r in rows if r['cohort']=='real']
    assert len(real)==751
    assert sum(r['target_status']=='unique' for r in real)==131
    assert len(rows)-len(real)==200

def test_manuscript_real_only_claims_match_decision_ledger():
    summary=json.loads((ROOT/'results/extended/summary.json').read_text())
    actual={r['policy']:r for r in summary['cohort_metrics'] if r['cohort']=='real_751'}
    assert (actual['E']['accepted'],actual['E']['incorrect_accepted'])==(1,0)
    assert (actual['D']['accepted'],actual['D']['incorrect_accepted'])==(26,16)
    assert summary['synthetic_overlap']['same_image_hash']==200
