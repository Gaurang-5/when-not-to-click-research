#!/usr/bin/env python3
"""Offline label/criterion sensitivity, ranking, skill and exploratory LTT recovery."""
import sys,json,hashlib,collections,itertools
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.extended_analysis import load
from scripts.analyze_label_studio_exports import parse_export
from scripts.evaluate_external_confirmatory import FrozenLogistic
from src.iteration3 import criterion,cluster_split,ranking_metrics,ltt_threshold
from src.metrics import iou
from src.policies import score,features
OUT=ROOT/'results/iteration3';OUT.mkdir(exist_ok=True)
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def sampling_ci(rows,fun,n_boot=1000):
 groups=sorted(set(r['source_image'] for r in rows));indexes=[np.array([i for i,r in enumerate(rows) if r['source_image']==g]) for g in groups];rng=np.random.default_rng(1729);vals=collections.defaultdict(list)
 for _ in range(n_boot):
  idx=np.concatenate([indexes[i] for i in rng.integers(0,len(groups),len(groups))]);m=fun(idx)
  for k,v in m.items():
   if v is not None and np.isfinite(v):vals[k].append(v)
 return {k:{'low':float(np.quantile(v,.025)),'high':float(np.quantile(v,.975)),'defined_replicates':len(v),'requested_replicates':n_boot} for k,v in vals.items()}
def detail(y,a):
 y=np.asarray(y,dtype=bool);a=np.asarray(a,dtype=bool);n=len(y);k=int(a.sum());bad=int((a&~y).sum())
 return {'n':n,'correct_localizations':int(y.sum()),'accepted':k,'incorrect_accepted':bad,'coverage':float(k/n) if n else None,'selective_risk':bad/k if k else None,'correct_accepted':k-bad}
def main():
 allrows,allpreds=load();ix=[i for i,r in enumerate(allrows) if r['cohort']=='real'];rows=[allrows[i] for i in ix];preds=[allpreds[i] for i in ix]
 f=json.loads((ROOT/'results/live_frozen_policy.json').read_text());model=FrozenLogistic(f['joint_coef'],f['joint_intercept']);names=['B','C','D','E','uniqueness'];scores={n:score(preds,n,model) for n in names}
 labelsdir=ROOT/'data/academic_2000/annotation_round_1/corrected_exports';aa,issues=parse_export(labelsdir/'annotator_a_corrected.json','A');bb,issuesb=parse_export(labelsdir/'annotator_b_corrected.json','B');assert not issues+issuesb
 manifests={r['case_id']:r for r in [json.loads(x) for x in (ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl').read_text().splitlines() if x.strip()]}
 def transform(case,b):
  t=manifests[case]['transform'];s=t['scale'];return [b[0]*s+t['pad_left'],b[1]*s+t['pad_top'],b[2]*s+t['pad_left'],b[3]*s+t['pad_top']]
 variants={'final':rows}
 for name,export in [('A_only',aa),('B_only',bb)]:
  variants[name]=[dict(r,target_status=export[r['case_id']]['status'],ground_truth_boxes=[transform(r['case_id'],b) for b in export[r['case_id']]['boxes_xyxy']]) for r in rows]
 variants['consensus_only']=[r for r in rows if aa[r['case_id']]['status']==bb[r['case_id']]['status'] and r['label_provenance']=='two_annotator_consensus']
 sensitivity=[]
 for name,rs in variants.items():
  indexes=[i for i,r in enumerate(rows) if r['case_id'] in {x['case_id'] for x in rs}];pr=[preds[i] for i in indexes]
  for mode in ['strict','iou03','center']:
   y=np.array([criterion(r,p,mode) for r,p in zip(rs,pr)])
   for n in names:
    a=scores[n][indexes]>=float(f['thresholds'][n]);sensitivity.append({'labels':name,'criterion':mode,'policy':n,**detail(y,a),'unique_n':sum(r['target_status']=='unique' for r in rs),'state_counts':dict(collections.Counter(r['target_status'] for r in rs))})
 pd.DataFrame(sensitivity).to_csv(OUT/'label_criterion_sensitivity.csv',index=False)
 human=[]
 for r in rows:
  a,b=aa[r['case_id']],bb[r['case_id']]
  if a['status']!='unique' or b['status']!='unique':continue
  x,y=a['boxes_xyxy'][0],b['boxes_xyxy'][0];xc,yc=(x[0]+x[2])/2,(x[1]+x[3])/2;xx,yy=(y[0]+y[2])/2,(y[1]+y[3])/2
  human.append({'case_id':r['case_id'],'source_image':r['source_image'],'iou':iou(x,y),'A_center_in_B':y[0]<=xc<=y[2] and y[1]<=yc<=y[3],'B_center_in_A':x[0]<=xx<=x[2] and x[1]<=yy<=x[3]})
 human_summary={'scope':'real cases labeled unique by both annotators only; agreement reference, not absolute model ceiling','n':len(human),'mean_iou':float(np.mean([h['iou'] for h in human])),'iou_pass_rate':{str(t):float(np.mean([h['iou']>=t for h in human])) for t in [.3,.5,.75]},'A_center_in_B':float(np.mean([h['A_center_in_B'] for h in human])),'B_center_in_A':float(np.mean([h['B_center_in_A'] for h in human]))}
 pd.DataFrame(human).to_csv(OUT/'human_geometry_agreement.csv',index=False)
 y=np.array([criterion(r,p) for r,p in zip(rows,preds)]);valid=np.array([p['status']=='ok' for p in preds]);ranking=[]
 for n in names:
  for scope,mask in [('valid_outputs',valid),('all_cases',np.ones(len(rows),dtype=bool)),('unique_valid',valid & np.array([r['target_status']=='unique' for r in rows]))]:
   idx=np.flatnonzero(mask);ss=np.where(np.isfinite(scores[n][idx]),scores[n][idx],-1.);ys=y[idx];rr=[rows[i] for i in idx]
   m=ranking_metrics(ys,ss);ci=sampling_ci(rr,lambda sub:ranking_metrics(ys[sub],ss[sub]))
   ranking.append({'policy':n,'scope':scope,**m,'cluster_ci':ci})
 pd.DataFrame(ranking).to_csv(OUT/'ranking_metrics.csv',index=False)
 split=cluster_split(rows);splitfile=ROOT/'reports/iteration3/real_cluster_split.json';encoded=json.dumps(split,indent=2)+'\n'
 if splitfile.exists() and splitfile.read_text()!=encoded:raise SystemExit('Frozen real split mismatch')
 splitfile.write_text(encoded)
 fit=np.array([split[r['case_id']]=='fit' for r in rows]);cal=np.array([split[r['case_id']]=='calibration' for r in rows]);test=np.array([split[r['case_id']]=='test' for r in rows])
 realmodel=LogisticRegression(C=1,max_iter=1000,random_state=1729).fit(features([p for i,p in enumerate(preds) if fit[i] and valid[i]]),y[fit&valid])
 scores['E_real_fit']=realmodel.predict_proba(features(preds))[:,1];scores['E_real_fit'][~valid]=-np.inf
 skill=[]
 for scope,mask in [('all_valid_real',valid),('exploratory_test_valid',test&valid)]:
  rate=float(y[mask].mean());calrate=float(y[cal&valid].mean());fitrate=float(y[fit&valid].mean())
  for n in ['B','E','E_real_fit']:
   raw=scores[n][mask];bs=float(np.mean((raw-y[mask])**2));ret=rate*(1-rate);calbs=float(np.mean((calrate-y[mask])**2));fitbs=float(np.mean((fitrate-y[mask])**2))
   skill.append({'scope':scope,'policy':n,'n':int(mask.sum()),'positive_rate':rate,'brier':bs,'retrospective_constant_brier':ret,'retrospective_brier_skill':1-bs/ret,'calibration_constant':calrate,'calibration_constant_brier':calbs,'calibration_constant_skill':1-bs/calbs,'fit_constant_brier':fitbs,'fit_constant_skill':1-bs/fitbs})
 pd.DataFrame(skill).to_csv(OUT/'brier_skill.csv',index=False)
 # Independently choose one case within each source cluster before looking at labels.
 one={}
 for i,r in enumerate(rows):
  key=hashlib.sha256(('independent_cluster_member|1729|'+r['case_id']).encode()).hexdigest()
  if r['source_image'] not in one or key<one[r['source_image']][0]:one[r['source_image']]=(key,i)
 unit=np.zeros(len(rows),dtype=bool);unit[[v[1] for v in one.values()]]=True
 policies=names+['E_real_fit'];grid=np.linspace(0,1,21).tolist();recovery=[];ltt_records=[]
 for n in policies:
  # empirical recovery is a descriptive comparator, no confidence guarantee.
  candidates=[]
  for t in grid:
   a=(scores[n]>=t)&cal;d=detail(y[cal],a[cal])
   if d['accepted'] and d['selective_risk']<=.1:candidates.append((d['accepted'],t))
  empirical=max(candidates)[1] if candidates else None
  a=(scores[n]>=empirical) if empirical is not None else np.zeros(len(rows),dtype=bool)
  recovery.append({'policy':n,'method':'empirical calibration risk <=10%; no guarantee','threshold':empirical,'test_scope':'all test cases descriptive',**detail(y[test],a[test])})
  ltt=ltt_threshold(scores[n][cal&unit],y[cal&unit],grid,alpha=.1,delta=.05/len(policies));ltt['policy']=n;ltt_records.append(ltt)
  t=ltt['threshold'];a=scores[n]>=t if t is not None else np.zeros(len(rows),dtype=bool)
  for scope,mask in [('one case per source cluster',test&unit),('all test cases descriptive',test)]:
   recovery.append({'policy':n,'method':'LTT alpha10%, family delta5% across policies and grid','threshold':t,'calibration_certified':ltt['certified'],'test_scope':scope,**detail(y[mask],a[mask])})
 pd.DataFrame(recovery).to_csv(OUT/'recalibration_recovery.csv',index=False)
 splitcounts={name:{'cases':int(mask.sum()),'clusters':len({r['source_image'] for i,r in enumerate(rows) if mask[i]}),'sampled_units':int((mask&unit).sum())} for name,mask in [('fit',fit),('calibration',cal),('test',test)]}
 protocol={'design':'post-hoc exploratory real cluster split; no untouched holdout claim','split':splitcounts,'split_sha256':hashlib.sha256(splitfile.read_bytes()).hexdigest(),'grid':grid,'target_conditional_error':.1,'family_delta':.05,'test_unit':'randomly hash-selected one member per independent source cluster; guarantees require i.i.d. cluster draws and protocol fixed before calibration, not fully verifiable in this retrospective cohort','E_real_fit_coef':realmodel.coef_.tolist(),'E_real_fit_intercept':realmodel.intercept_.tolist(),'fit_only':True}
 write('reviewer_analysis_summary.json',{'state':'OFFLINE_ANALYSES_EXECUTED','design':protocol,'human_reference':human_summary,'skill':skill,'ranking':ranking,'recovery':recovery,'ltt_details':ltt_records,'sensitivity':sensitivity})
 print(json.dumps({'state':'OFFLINE_ANALYSES_EXECUTED','split':splitcounts,'human_reference':human_summary,'skill':skill,'recovery':recovery},indent=2))
if __name__=='__main__':main()
