#!/usr/bin/env python3
"""Evaluate frozen synthetic-selected policies once on the external cohort."""

import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.metrics import correctness, summarize
from src.policies import decide, features, score
from src.statistical_tests import holm, paired_randomization

class FrozenLogistic:
    def __init__(self,coef,intercept):
        self.coef=np.asarray(coef,dtype=float)[0]; self.intercept=float(np.asarray(intercept,dtype=float)[0])
    def predict_proba(self,x):
        z=np.asarray(x,dtype=float)@self.coef+self.intercept; p=1/(1+np.exp(-z)); return np.column_stack([1-p,p])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',type=Path,default=ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl')
    ap.add_argument('--calls',type=Path,default=ROOT/'results/external_confirmatory_calls.jsonl')
    ap.add_argument('--output-dir',type=Path,default=ROOT/'results/external_confirmatory')
    args=ap.parse_args()
    if not args.manifest.exists() or not args.calls.exists(): raise SystemExit('External collection is incomplete or has not started.')
    rows=[json.loads(x) for x in args.manifest.read_text().splitlines() if x.strip()]
    by={}
    attempts=[]
    for line in args.calls.read_text().splitlines():
        r=json.loads(line); attempts.append(r)
        case_id=r['case_id']
        if case_id not in by or r.get('status')=='ok' or by[case_id].get('status')!='ok':
            by[case_id]=r
    ids={r['case_id'] for r in rows}
    if set(by)!=ids:
        raise SystemExit(f'Need at least one attempted output per case: expected={len(ids)}, attempted={len(set(by)&ids)}')
    preds=[by[r['case_id']] for r in rows]
    freeze_path=ROOT/'results/live_frozen_policy.json'; sha_path=ROOT/'results/live_frozen_policy.sha256'
    if hashlib.sha256(freeze_path.read_bytes()).hexdigest()!=sha_path.read_text().split()[0]: raise SystemExit('Frozen policy hash mismatch')
    freeze=json.loads(freeze_path.read_text()); model=FrozenLogistic(freeze['joint_coef'],freeze['joint_intercept'])
    policies=['A','B','C','D','E','presence','uniqueness','presence_uniqueness']
    table=[]; accepted={}; actions={}
    for name in policies:
        values=score(preds,name,model); a,act=decide(preds,values,float(freeze['thresholds'][name]))
        accepted[name]=a; actions[name]=act
        table.append({'policy':name,'threshold':freeze['thresholds'][name],**summarize(rows,preds,a,act)})
    comparisons=[]
    for category in ['absent','multiple']:
        idx=[i for i,r in enumerate(rows) if r['target_status']==category]
        if not idx: continue
        sub=[rows[i] for i in idx]; diff=accepted['D'][idx].astype(int)-accepted['B'][idx].astype(int)
        # Each source screenshot is a cluster; the randomization helper reads template_id.
        for r in sub: r['template_id']=r['source_image']
        randomization=paired_randomization(sub,diff,n_perm=10000)
        comparisons.append({
            'endpoint':category,
            'comparison':'D_minus_B',
            'case_weighted_difference':float(diff.mean()),
            'cluster_weighted_difference':randomization.pop('difference'),
            **randomization,
        })
    adjusted=holm([r['p_cluster_sign'] for r in comparisons]) if comparisons else []
    for row,p in zip(comparisons,adjusted): row['p_holm']=p
    latencies=[r['latency_ms'] for r in attempts if isinstance(r.get('latency_ms'),(int,float))]
    usage_records=[(r.get('raw_response') or {}).get('usage') or r.get('usage') or {} for r in attempts]
    input_tokens=sum(u.get('input_tokens',0) for u in usage_records)
    output_tokens=sum(u.get('output_tokens',0) for u in usage_records)
    operations={
        'network_attempts':len(attempts),
        'auth_rejected_attempts':sum(r.get('http_status') in (401,403) for r in attempts),
        'billable_http_200_attempts':sum(r.get('http_status')==200 for r in attempts),
        'input_tokens':input_tokens,
        'output_tokens':output_tokens,
        'estimated_cost_usd':round(input_tokens*0.042/1_000_000,12),
        'mean_latency_ms':float(np.mean(latencies)),
        'median_latency_ms':float(np.median(latencies)),
        'p95_latency_ms':float(np.percentile(latencies,95)),
    }
    args.output_dir.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(table).to_csv(args.output_dir/'policy_metrics.csv',index=False)
    summary={'state':'EVALUATED','provenance':'real Jev API responses on frozen human-adjudicated labels',
             'cases':len(rows),'network_attempts':len(attempts),
             'successful_outputs':sum(p.get('status')=='ok' for p in preds),
             'failed_outputs':sum(p.get('status')!='ok' for p in preds),
             'operations':operations,
             'failure_reasons':{
                 str(reason): int(count)
                 for reason,count in pd.Series([
                     p.get('error_message','unknown') for p in preds
                     if p.get('status')!='ok'
                 ]).value_counts().items()
             },
             'policy_metrics':{r['policy']:r for r in table},
             'primary_comparisons':comparisons}
    (args.output_dir/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'state':'EVALUATED','cases':len(rows),'output':str(args.output_dir)}))
if __name__=='__main__': main()
