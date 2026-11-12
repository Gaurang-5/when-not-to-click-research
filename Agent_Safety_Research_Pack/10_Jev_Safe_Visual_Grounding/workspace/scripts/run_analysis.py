"""Frozen configuration -> validation -> dev fit -> calibration threshold -> test evaluation."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.validate_data import load,validate
from src.policies import score,decide
from src.calibration import fit_joint,coverage_threshold,reliability
from src.metrics import correctness,summarize,risk_curve
from src.statistical_tests import cluster_bootstrap,paired_randomization,holm
from src.plots import render

def main():
 config=json.loads((ROOT/'configs/experiment.json').read_text());rows=load(ROOT/'data/pilot_cases.jsonl');print(validate(rows,ROOT));predictions=load(ROOT/'data/demo_predictions.jsonl')
 assert len({p['case_id'] for p in predictions})==len(predictions),'duplicate predictions'
 assert all(p['provenance']=='simulated_fixture' for p in predictions),'This entry point is explicitly demo-only'
 lookup={p['case_id']:p for p in predictions};assert set(lookup)=={r['case_id'] for r in rows}
 split={s:([r for r in rows if r['split']==s],[lookup[r['case_id']] for r in rows if r['split']==s]) for s in ['dev','calibration','test']}
 dr,dp=split['dev'];cr,cp=split['calibration'];tr,tp=split['test'];joint=fit_joint(dp,correctness(dr,dp)[0]);policies=['A','B','C','D','E','presence','uniqueness','presence_uniqueness'];out=ROOT/'results';thresholds={}
 # Freeze thresholds before computing ANY test outcomes; manifest records exact config and fit.
 for pol in policies:thresholds[pol]=0. if pol=='A' else coverage_threshold(score(cp,pol,joint),config['target_calibration_coverage'])
 freeze={'config_sha256':hashlib.sha256((ROOT/'configs/experiment.json').read_bytes()).hexdigest(),'thresholds':{k:v if np.isfinite(v) else 'Infinity' for k,v in thresholds.items()},'joint_coef':joint.coef_.tolist(),'joint_intercept':joint.intercept_.tolist(),'training_split':'dev','threshold_split':'calibration','test_used_for_selection':False,'provenance':'simulated_fixture'}
 (out/'frozen_policy.json').write_text(json.dumps(freeze,indent=2))
 table=[];strata=[];curves={};intervals=[];accepted={};actions_by={};scores_by={};correct,overlap=correctness(tr,tp)
 for pol in policies:
  sc=score(tp,pol,joint);acc,actions=decide(tp,sc,thresholds[pol]);accepted[pol]=acc;actions_by[pol]=actions;scores_by[pol]=sc
  table.append({'policy':pol,**summarize(tr,tp,acc,actions)});curves[pol]=risk_curve(tr,tp,sc)
  for group in ['target_status','template_id','layout_family','target_size','clutter','difficulty']:
   for value in sorted({r[group] for r in tr}):
    idx=[i for i,r in enumerate(tr) if r[group]==value];strata.append({'policy':pol,'stratum':group,'value':value,**summarize([tr[i] for i in idx],[tp[i] for i in idx],acc[idx],[actions[i] for i in idx])})
  for metric in ['coverage','selective_risk','marginal_incorrect_action_rate','absent_false_accept_rate','ambiguous_wrong_accept_rate']:
   def stat(idx):return summarize([tr[i] for i in idx],[tp[i] for i in idx],acc[idx],[actions[i] for i in idx])[metric]
   intervals.append({'policy':pol,'metric':metric,**cluster_bootstrap(tr,stat,n_boot=config['bootstrap_replicates'])})
 rel={};presence=np.array([p['presence_confidence'] if p['status']=='ok' else np.nan for p in tp]);box=np.array([p['box_confidence'] if p['status']=='ok' else np.nan for p in tp]);visible=np.array([r['target_status'] not in ['absent','offscreen'] for r in tr]);jointprob=joint.predict_proba(__import__('src.policies',fromlist=['features']).features(tp))[:,1];jointprob[np.array([p['status']!='ok' for p in tp])]=np.nan
 for name,sc,lab in [('presence',presence,visible),('box_event',box,correct),('joint',jointprob,correct)]:
  rel[name+'_all']=reliability(sc,lab)
  for cat in ['absent','multiple','unique']:
   idx=np.array([r['target_status']==cat for r in tr]);rel[name+'_'+cat]=reliability(sc[idx],lab[idx])
 comparisons=[]
 for cat in ['absent','multiple']:
  idx=[i for i,r in enumerate(tr) if r['target_status']==cat];sub=[tr[i] for i in idx];difference=accepted['D'][idx].astype(int)-accepted['B'][idx].astype(int)
  comparisons.append({'endpoint':cat,'comparison':'D_minus_B','n':len(idx),**paired_randomization(sub,difference,n_perm=config['randomization_replicates']), 'difference_ci':cluster_bootstrap(sub,lambda ii:float(difference[ii].mean()))})
 for c,p in zip(comparisons,holm([c['p_cluster_sign'] for c in comparisons])):c['p_holm']=p
 pd.DataFrame(table).to_csv(out/'demo_policy_metrics.csv',index=False);pd.DataFrame(strata).to_csv(out/'demo_stratified_metrics.csv',index=False);pd.DataFrame(intervals).to_csv(out/'demo_confidence_intervals.csv',index=False)
 (out/'demo_calibration.json').write_text(json.dumps(rel,indent=2));(out/'demo_comparisons.json').write_text(json.dumps(comparisons,indent=2));(out/'demo_risk_curves.json').write_text(json.dumps(curves,indent=2))
 errors=[{'case_id':r['case_id'],'status':r['target_status'],'policy':pol,'decision':actions_by[pol][i],'incorrect_accept':bool(accepted[pol][i] and not correct[i]),'iou':float(overlap[i])} for pol in policies for i,r in enumerate(tr) if (accepted[pol][i] and not correct[i]) or (not accepted[pol][i] and correct[i])]
 pd.DataFrame(errors).to_csv(out/'demo_error_analysis.csv',index=False)
 render(curves,rel,table,overlap[[r['target_status']=='unique' for r in tr]],out)
 summary={'provenance':'SIMULATED FIXTURES ONLY; NOT JEV RESULTS','cases':len(rows),'test_cases':len(tr),'real_api_calls':0,'fixture_errors':sum(p['status']!='ok' for p in predictions),'split_counts':{s:len(v[0]) for s,v in split.items()},'templates':25,'test_templates':10,'test_layout_families':2,'predictions_missing':0,'independent_human_annotators':0,'policy_metrics':table,'primary_comparisons':comparisons}
 (out/'execution_summary.json').write_text(json.dumps(summary,indent=2));print(pd.DataFrame(table)[['policy','accepted','coverage','selective_risk','marginal_incorrect_action_rate','absent_false_accept_rate','ambiguous_wrong_accept_rate']].to_string(index=False))
if __name__=='__main__':main()
