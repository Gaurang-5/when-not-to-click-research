#!/usr/bin/env python3
"""Evaluate completed repeat/prompt cohorts and local baseline; mark partial ones."""
import sys,json,collections,hashlib,datetime
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.extended_analysis import load
from scripts.evaluate_external_confirmatory import FrozenLogistic
from src.iteration3 import criterion,ranking_metrics
from src.policies import score,decide
from src.metrics import summarize,iou
OUT=ROOT/'results/iteration3'
def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
def summary(rows,preds,name):
 f=json.loads((ROOT/'results/live_frozen_policy.json').read_text());model=FrozenLogistic(f['joint_coef'],f['joint_intercept']);metrics=[]
 for n in ['A','B','C','D','E','uniqueness']:
  ss=score(preds,n,model);a,act=decide(preds,ss,float(f['thresholds'][n]));metrics.append({'cohort':name,'policy':n,**summarize(rows,preds,a,act)})
 return metrics

def main():
 rows,original=load();realrows=[r for r in rows if r['cohort']=='real'];byoriginal={r['case_id']:p for r,p in zip(rows,original)};realids={r['case_id'] for r in realrows}
 results={'snapshot_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'PARTIAL','repeat_progress':{},'completed_metrics':[],'raw_usage':{},'baseline':{'state':'NOT_STARTED'}};sets={('original',1):{k:v for k,v in byoriginal.items() if k in realids}}
 attempts=read(OUT/'jev_repeated_calls.jsonl')
 for r in attempts:
  if r.get('http_status') in [401,403]:continue
  key=(r['variant'],r['repeat']);sets.setdefault(key,{})[r['case_id']]=r
 for variant in ['original','literal','conservative']:
  repeats=range(1,6) if variant=='original' else [1]
  for repeat in repeats:
   by=sets.get((variant,repeat),{});count=len(set(by)&realids);results['repeat_progress'][f'{variant}:r{repeat}']={'attempted':count,'expected':len(realrows),'complete':count==len(realrows),'valid_outputs':sum(p.get('status')=='ok' for k,p in by.items() if k in realids),'failures':sum(p.get('status')!='ok' for k,p in by.items() if k in realids),'latency_mean_ms':float(np.mean([p['latency_ms'] for k,p in by.items() if k in realids])) if count else None}
   if count==len(realrows):results['completed_metrics']+=summary(realrows,[by[r['case_id']] for r in realrows],f'{variant}:r{repeat}')
 usage=[(r.get('raw_response') or {}).get('usage') or {} for r in attempts]
 results['jev_failure_messages']=dict(collections.Counter(r.get('error_message','unspecified') for r in attempts if r['status']!='ok'))
 results['raw_usage']={'network_attempts':len(attempts),'input_tokens':sum(u.get('input_tokens',0) for u in usage),'output_tokens':sum(u.get('output_tokens',0) for u in usage)};results['raw_usage']['estimated_cost_usd']=results['raw_usage']['input_tokens']*.042/1e6
 completed_original=[sets[('original',i)] for i in range(1,6) if len(sets.get(('original',i),{}))==751]
 if len(completed_original)==5:
  consistency=[];decision_arrays={}
  frozen=json.loads((ROOT/'results/live_frozen_policy.json').read_text());fmodel=FrozenLogistic(frozen['joint_coef'],frozen['joint_intercept'])
  for name in ['B','D','E']:
   decision_arrays[name]=np.array([score([c[r['case_id']] for r in realrows],name,fmodel)>=float(frozen['thresholds'][name]) for c in completed_original])
  pairwise_box_iou=[]
  for row in realrows:
   ps=[b[row['case_id']] for b in completed_original];valid=[p for p in ps if p['status']=='ok'];correct=[criterion(row,p) for p in ps]
   boxes=[p['predicted_box'] for p in valid];pairwise_box_iou +=[iou(a,b) for i,a in enumerate(boxes) for b in boxes[i+1:]];counts=collections.Counter(p.get('match_choice','error') for p in ps)
   consistency.append({'case_id':row['case_id'],'valid_runs':len(valid),'correct_runs':sum(correct),'match_label_agreement':max(counts.values())/5,'distinct_boxes':len(set(tuple(b) for b in boxes))})
  pd.DataFrame(consistency).to_csv(OUT/'jev_repeat_case_consistency.csv',index=False)
  results['decision_repeatability']={'case_count':len(realrows),'policy_acceptance_flip_cases':{k:int(np.any(a!=a[0],axis=0).sum()) for k,a in decision_arrays.items()},'valid_box_pair_count':len(pairwise_box_iou),'mean_valid_pair_box_iou':float(np.mean(pairwise_box_iou)),'modal_label_fraction_note':'Mean of each case modal match-count label frequency divided by five; includes failed outputs as an error label.'}
  results['repeat_consistency']={'cases':751,'correctness_changes':sum(0<c['correct_runs']<5 for c in consistency),'mean_match_label_agreement':float(np.mean([c['match_label_agreement'] for c in consistency]))}
 baseline=read(OUT/'qwen_baseline_calls.jsonl');by={r['case_id']:r for r in baseline};real={k:p for k,p in by.items() if k in realids}
 results['baseline']={'state':'COMPLETE' if len(by)==951 else 'PARTIAL' if by else 'NOT_STARTED','attempted':len(by),'expected':951,'real_attempted':len(real),'ok':sum(p['status']=='ok' for p in by.values()),'cost_usd':None,'cost_note':'local GPU/energy unpriced; zero cloud API calls','latency_mean_ms':float(np.mean([p['latency_ms'] for p in by.values()])) if by else None,'latency_p95_ms':float(np.percentile([p['latency_ms'] for p in by.values()],95)) if by else None}
 if len(by)==951:
  expected_ids={r['case_id'] for r in rows}
  if len(baseline)!=951 or set(by)!=expected_ids:raise SystemExit('Baseline IDs are duplicated or differ from the frozen cohort.')
  protocol_hash=hashlib.sha256((ROOT/'reports/iteration3/baseline_protocol.json').read_bytes()).hexdigest()
  if {r['protocol_sha256'] for r in baseline}!={protocol_hash}:raise SystemExit('Baseline protocol hash mismatch.')
  if len({r['model_digest'] for r in baseline})!=1:raise SystemExit('Baseline model digest changed.')
  if not all(by[r['case_id']]['image_sha256']==byoriginal[r['case_id']]['image_sha256'] for r in rows):raise SystemExit('Model input image hashes differ.')
  results['baseline']['same_input_images_verified']=951
  results['baseline']['model_digest']=baseline[0]['model_digest']
  raw_path=OUT/'qwen_baseline_calls.jsonl';raw_hash=hashlib.sha256(raw_path.read_bytes()).hexdigest();results['baseline']['raw_sha256']=raw_hash
  sidecar=raw_path.with_suffix('.sha256')
  if sidecar.exists() and sidecar.read_text().split()[0]!=raw_hash:raise SystemExit('Completed Qwen log changed after freeze.')
  sidecar.write_text(raw_hash+'  '+raw_path.name+'\n')
  # Prompted confidences are evaluated separately, with no claim of native calibration.
  # Never transfer Jev-fitted logistic coefficients to Qwen verbalized probabilities.
  results['baseline']['metrics_note']='Forced geometry and fixed one-label semantic gate only; no Jev-trained logistic applied to Qwen self-reports.'
  results['baseline']['primary_metrics']={}
  for name,rr,pp in [('Jev',realrows,[byoriginal[r['case_id']] for r in realrows]),('Qwen',realrows,[real[r['case_id']] for r in realrows])]:
   results['baseline']['primary_metrics'][name]={'n':len(rr),'valid_outputs':sum(p['status']=='ok' for p in pp),'unique_n':sum(r['target_status']=='unique' for r in rr),'strict_correct':sum(criterion(r,p,'strict') for r,p in zip(rr,pp)),'iou03_correct':sum(criterion(r,p,'iou03') for r,p in zip(rr,pp)),'center_correct':sum(criterion(r,p,'center') for r,p in zip(rr,pp))}
   # Abstention using a prompted semantic gate is fixed before seeing baseline results.
   a=np.array([p['status']=='ok' and p.get('match_choice')=='one' for p in pp]);ys=np.array([criterion(r,p) for r,p in zip(rr,pp)])
   results['baseline']['primary_metrics'][name]['one_label_gate']={'accepted':int(a.sum()),'errors':int((a&~ys).sum())}

  results['baseline']['deployment_comparison']={}
  for name,rr,pp in [('Jev',rows,[byoriginal[r['case_id']] for r in rows]),('Qwen',rows,[by[r['case_id']] for r in rows])]:
   times=[p['latency_ms'] for p in pp]
   results['baseline']['deployment_comparison'][name]={'attempts':len(pp),'valid_outputs':sum(p['status']=='ok' for p in pp),'failure_outputs':sum(p['status']!='ok' for p in pp),'latency_mean_ms':float(np.mean(times)),'latency_p95_ms':float(np.percentile(times,95)),'api_cost_estimate_usd':sum(((p.get('raw_response') or {}).get('usage') or {}).get('input_tokens',0) for p in pp)*.042/1e6 if name=='Jev' else 0,'total_economic_cost_usd':None,'cost_note':'Jev recorded token rate estimate, not invoice; local Qwen hardware and electricity unpriced.'}
  ledger=[]
  for row in realrows:
   cid=row['case_id'];j=byoriginal[cid];q=by[cid]
   ledger.append({'case_id':cid,'source_image':row['source_image'],'target_status':row['target_status'],'Jev_status':j['status'],'Qwen_status':q['status'],**{name+'_'+mode:criterion(row,pred,mode) for name,pred in [('Jev',j),('Qwen',q)] for mode in ['strict','iou03','center']}})
  pd.DataFrame(ledger).to_csv(OUT/'same_data_model_case_ledger.csv',index=False)
  # Apply each human reference to both models, without altering frozen labels.
  from scripts.analyze_label_studio_exports import parse_export
  labeldir=ROOT/'data/academic_2000/annotation_round_1/corrected_exports';aa,ia=parse_export(labeldir/'annotator_a_corrected.json','A');bb,ib=parse_export(labeldir/'annotator_b_corrected.json','B')
  if ia or ib:raise SystemExit('Human reference export failed validation.')
  manifest={r['case_id']:r for r in read(ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl')}
  references={'final':realrows,'consensus_only':[r for r in realrows if r['label_provenance']=='two_annotator_consensus']}
  for name,export in [('A_only',aa),('B_only',bb)]:
   refs=[]
   for row in realrows:
    cid=row['case_id'];t=manifest[cid]['transform'];scale=t['scale'];boxes=[[b[0]*scale+t['pad_left'],b[1]*scale+t['pad_top'],b[2]*scale+t['pad_left'],b[3]*scale+t['pad_top']] for b in export[cid]['boxes_xyxy']]
    refs.append(dict(row,target_status=export[cid]['status'],ground_truth_boxes=boxes))
   references[name]=refs
  label_sensitivity=[]
  for labelname,rr in references.items():
   unique=sum(r['target_status']=='unique' for r in rr)
   for modelname,pp in [('Jev',byoriginal),('Qwen',by)]:
    for mode in ['strict','iou03','center']:
     correct=sum(criterion(r,pp[r['case_id']],mode) for r in rr)
     label_sensitivity.append({'labels':labelname,'model':modelname,'criterion':mode,'n':len(rr),'unique_n':unique,'correct':correct,'unique_accuracy':correct/unique if unique else None})
  results['baseline']['label_sensitivity']=label_sensitivity
  pd.DataFrame(label_sensitivity).to_csv(OUT/'same_data_label_sensitivity.csv',index=False)
  from scripts.reviewer_analysis import sampling_ci
  jpred=[byoriginal[r['case_id']] for r in realrows];qpred=[real[r['case_id']] for r in realrows]
  def compare(indices):
   out={};unique=np.array([realrows[i]['target_status']=='unique' for i in indices])
   for mode in ['strict','iou03','center']:
    j=np.array([criterion(realrows[i],jpred[i],mode) for i in indices]);q=np.array([criterion(realrows[i],qpred[i],mode) for i in indices]);out[mode+'_unique_accuracy_difference_Qwen_minus_Jev']=float((q[unique].astype(float)-j[unique].astype(float)).mean()) if unique.any() else None
   return out
  results['baseline']['paired_geometry_comparison']={'estimates':compare(np.arange(len(realrows))),'source_cluster_ci':sampling_ci(realrows,compare,n_boot=2000),'note':'Paired by identical input and human reference; geometry criteria are separate exploratory endpoints, no superiority test or multiplicity-adjusted claim.'}
  results['baseline']['failure_counts']=dict(collections.Counter(p.get('error_message','unspecified') for p in by.values() if p['status']!='ok'))
  timed=list(by.values());warm=[p['latency_ms'] for p in timed[1:]]
  results['baseline']['latency_after_first_request_mean_ms']=float(np.mean(warm));results['baseline']['latency_first_request_ms']=timed[0]['latency_ms']
 if all(r['complete'] for r in results['repeat_progress'].values()) and results['baseline']['state']=='COMPLETE':results['state']='COMPLETE'
 results['jev_collection_state']='COMPLETE' if all(r['complete'] for r in results['repeat_progress'].values()) else 'PARTIAL'
 if results['jev_collection_state']=='COMPLETE':
  raw_path=OUT/'jev_repeated_calls.jsonl';raw_hash=hashlib.sha256(raw_path.read_bytes()).hexdigest();results['jev_raw_sha256']=raw_hash
  sidecar=raw_path.with_suffix('.sha256')
  if sidecar.exists() and sidecar.read_text().split()[0]!=raw_hash:raise SystemExit('Completed Jev raw log changed after freeze.')
  sidecar.write_text(raw_hash+'  '+raw_path.name+'\n')
 pd.DataFrame(results['completed_metrics']).to_csv(OUT/'jev_completed_repeat_metrics.csv',index=False)
 (OUT/'collection_summary.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'state':results['state'],'repeat_progress':results['repeat_progress'],'baseline':{k:v for k,v in results['baseline'].items() if k!='metrics'}},indent=2))
if __name__=='__main__':main()
