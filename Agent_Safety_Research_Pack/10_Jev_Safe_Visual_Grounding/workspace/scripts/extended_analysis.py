#!/usr/bin/env python3
"""Offline, post-hoc diagnostics. Never imports the API client or issues requests."""
import sys,json,hashlib,math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.evaluate_external_confirmatory import FrozenLogistic
from src.policies import score,decide
from src.metrics import correctness,summarize,risk_curve
from src.calibration import reliability,coverage_threshold
from src.statistical_tests import paired_randomization,holm
OUT=ROOT/'results/extended';OUT.mkdir(exist_ok=True,parents=True)
POLICIES=['A','B','C','D','E','presence','uniqueness','presence_uniqueness']
def read(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def load():
 rows=read(ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl')
 meta={r['case_id']:r for r in read(ROOT/'data/academic_2000/manifest.jsonl')}
 labels={r['case_id']:r for r in read(ROOT/'data/academic_2000/annotation_round_1/frozen_labels/final_labels.jsonl')}
 comparison=pd.read_csv(ROOT/'data/academic_2000/annotation_round_1/corrected_analysis/case_comparison.csv').set_index('case_id')
 by={}
 for r in read(ROOT/'results/external_confirmatory_calls.jsonl'):
  if r['case_id'] not in by or r.get('status')=='ok' or by[r['case_id']].get('status')!='ok':by[r['case_id']]=r
 for r in rows:
  m=meta[r['case_id']]; c=comparison.loc[r['case_id']]
  r.update(platform=m['platform'],source_dataset=m['source_dataset'],element_type=m['element_type'],
    label_provenance=labels[r['case_id']]['label_provenance'],
    confidence='low' if 'low' in [c.annotator_a_confidence,c.annotator_b_confidence] else 'medium' if 'medium' in [c.annotator_a_confidence,c.annotator_b_confidence] else 'high',
    cohort='real' if r['case_id'].startswith('ssv2v_') else 'synthetic_reuse')
  area=sum((b[2]-b[0])*(b[3]-b[1]) for b in r['ground_truth_boxes'])/(r['width']*r['height'])
  r['instruction_length']='1-3 words' if len(r['instruction'].split())<=3 else '4-7 words' if len(r['instruction'].split())<=7 else '8+ words'
  r['target_size']='not_unique' if r['target_status']!='unique' else 'small (<0.1%)' if area<.001 else 'medium (0.1-1%)' if area<.01 else 'large (>=1%)'
 return rows,[by[r['case_id']] for r in rows]
def bootstrap(rows,correct,accepted,n_boot=2000):
 groups=sorted(set(r['source_image'] for r in rows)); gi={g:i for i,g in enumerate(groups)}
 states=np.array([r['target_status'] for r in rows]);a=np.asarray(accepted);y=np.asarray(correct)
 vals=np.column_stack([np.ones(len(rows)),a,a&~y,states=='absent',a&(states=='absent'),states=='multiple',a&(states=='multiple'),states=='unique',a&y&(states=='unique')]).astype(float)
 agg=np.zeros((len(groups),9))
 np.add.at(agg,[gi[r['source_image']] for r in rows],vals)
 rng=np.random.default_rng(1729); draws=rng.integers(0,len(groups),(n_boot,len(groups)))
 totals=agg[draws].sum(axis=1)
 result={}
 for key,num,den in [('coverage',1,0),('selective_risk',2,1),('marginal_incorrect_action_rate',2,0),('absent_false_accept_rate',4,3),('ambiguous_wrong_accept_rate',6,5),('unique_useful_automation_rate',8,7)]:
  good=totals[:,den]>0;v=totals[good,num]/totals[good,den]
  result[key]={'low':float(np.quantile(v,.025)) if len(v) else None,'high':float(np.quantile(v,.975)) if len(v) else None,'defined_replicates':int(good.sum()),'replicates':n_boot}
 return result

def main():
 rows,preds=load();f=json.loads((ROOT/'results/live_frozen_policy.json').read_text());model=FrozenLogistic(f['joint_coef'],f['joint_intercept'])
 scores={n:score(preds,n,model) for n in POLICIES}
 # New entropy baselines are explicitly exploratory: thresholds use only the
 # original synthetic calibration responses, never external labels.
 def entropy_score(ps,require_one=False):
  values=[]
  for p in ps:
   probs=p.get('match_probabilities') or {}
   if p.get('status')!='ok' or len(probs)!=3 or (require_one and p.get('match_choice')!='one'):
    values.append(-np.inf);continue
   values.append(1+sum(v*np.log(v) for v in probs.values() if v>0)/np.log(3))
  return np.array(values)
 pilot_rows=read(ROOT/'data/pilot_cases.jsonl');pilot_by={r['case_id']:r for r in read(ROOT/'results/live_calls.jsonl')}
 calibration_preds=[pilot_by[r['case_id']] for r in pilot_rows if r['split']=='calibration']
 exploratory={}
 for name,one in [('entropy',False),('entropy_one',True)]:
  scores[name]=entropy_score(preds,one);t=coverage_threshold(entropy_score(calibration_preds,one),.3)
  f['thresholds'][name]=float(t);exploratory[name]={'threshold':float(t) if np.isfinite(t) else 'Infinity','selection':'original synthetic calibration only; introduced after seeing external results'}
 policies=POLICIES+list(exploratory)
 decisions={n:decide(preds,scores[n],float(f['thresholds'][n])) for n in policies};correct,ov=correctness(rows,preds)
 masks={'mixed_951':np.ones(len(rows),dtype=bool),'real_751':np.array([r['cohort']=='real' for r in rows]),'synthetic_reuse_200':np.array([r['cohort']!='real' for r in rows])}
 metrics=[];cis={};comparisons={}
 for cohort,mask in masks.items():
  idx=np.flatnonzero(mask); sub=[rows[i] for i in idx];pr=[preds[i] for i in idx];cis[cohort]={}
  for n in policies:
   a,act=decisions[n];m=summarize(sub,pr,a[idx],[act[i] for i in idx]);metrics.append({'cohort':cohort,'policy':n,**m})
   if n in ['B','D','E','uniqueness']:cis[cohort][n]=bootstrap(sub,correct[idx],a[idx])
  comps=[]
  for state in ['absent','multiple']:
   ids=[i for i in idx if rows[i]['target_status']==state]
   if not ids:continue
   ss=[dict(rows[i],template_id=rows[i]['source_image']) for i in ids];d=decisions['D'][0][ids].astype(int)-decisions['B'][0][ids].astype(int)
   test=paired_randomization(ss,d);test['cluster_weighted_difference']=test.pop('difference')
   comps.append({'endpoint':state,'case_weighted_difference':float(d.mean()),**test})
  for c,p in zip(comps,holm([x['p_cluster_sign'] for x in comps])):c['p_holm']=p
  comparisons[cohort]=comps
 pd.DataFrame(metrics).to_csv(OUT/'cohort_metrics.csv',index=False)
 strat=[]
 for field in ['platform','target_status','target_size','confidence','label_provenance','element_type','source_dataset','instruction_length']:
  for value in sorted(set(r[field] for r in rows)):
   ix=[i for i,r in enumerate(rows) if r[field]==value]
   for n in ['B','D','E','uniqueness']:
    a,act=decisions[n];strat.append({'field':field,'stratum':value,'policy':n,**summarize([rows[i] for i in ix],[preds[i] for i in ix],a[ix],[act[i] for i in ix])})
 pd.DataFrame(strat).to_csv(OUT/'stratified_metrics.csv',index=False)
 # Per-case ledger supports every published number and selected illustration.
 ledger=[]
 for i,r in enumerate(rows):
  ledger.append({**{k:r[k] for k in ['case_id','cohort','platform','target_status','target_size','confidence','label_provenance']},'correct':bool(correct[i]),'iou':float(ov[i]),'valid':preds[i]['status']=='ok',**{n+'_accept':bool(decisions[n][0][i]) for n in POLICIES}})
 pd.DataFrame(ledger).to_csv(OUT/'case_ledger.csv',index=False)
 # Audit the synthetic reuse against the policy development/calibration/test manifest.
 pilot={r['case_id']:r for r in read(ROOT/'data/pilot_cases.jsonl')};overlap=[]
 for r in rows:
  if r['cohort']!='synthetic_reuse':continue
  old=pilot[r['case_id'].removeprefix('synthetic_')]
  path=ROOT/r['source_image'].split('?d=')[-1]
  same=hashlib.sha256(path.read_bytes()).hexdigest()==old['screenshot_sha256']
  overlap.append({'case_id':r['case_id'],'pilot_split':old['split'],'same_image_hash':same,'same_instruction':old['instruction']==r['instruction']})
 pd.DataFrame(overlap).to_csv(OUT/'synthetic_overlap_audit.csv',index=False)
 # Calibration: presence -> at least one visible match; uniqueness -> unique state;
 # box and logistic -> primary safe-localization correctness. Valid responses only.
 cal={};fig,axes=plt.subplots(1,2,figsize=(10,4))
 for ax,(cohort,mask) in zip(axes,[('mixed_951',masks['mixed_951']),('real_751',masks['real_751'])]):
  cal[cohort]={};ax.plot([0,1],[0,1],'--',color='gray',linewidth=1)
  for n,label in [('presence','visible presence'),('uniqueness','unique target'),('B','correct localization'),('E','correct localization')]:
   ix=[i for i in np.flatnonzero(mask) if preds[i]['status']=='ok']
   target=np.array([rows[i]['target_status'] in ['unique','multiple'] for i in ix]) if n=='presence' else np.array([rows[i]['target_status']=='unique' for i in ix]) if n=='uniqueness' else correct[ix]
   rel=reliability(scores[n][ix],target);rel['target']=label;cal[cohort][n]=rel
   bins=[b for b in rel['bins'] if b['n']];ax.plot([b['confidence'] for b in bins],[b['frequency'] for b in bins],marker='o',label=n)
  ax.set(title=cohort,xlabel='Reported confidence',ylabel='Observed target frequency',xlim=(0,1),ylim=(0,1));ax.legend()
 fig.tight_layout();fig.savefig(OUT/'calibration.png',dpi=200);fig.savefig(OUT/'calibration.pdf');plt.close(fig)
 curves=[];fig,axes=plt.subplots(1,2,figsize=(10,4))
 for ax,(cohort,mask) in zip(axes,[('mixed_951',masks['mixed_951']),('real_751',masks['real_751'])]):
  ix=np.flatnonzero(mask)
  for n in ['B','C','D','E','uniqueness','entropy_one']:
   curve=risk_curve([rows[i] for i in ix],[preds[i] for i in ix],scores[n][ix]);curves += [{'cohort':cohort,'policy':n,**v} for v in curve]
   ax.step([v['coverage'] for v in curve],[v['risk'] for v in curve],where='post',label=n)
   a=decisions[n][0][ix];ax.scatter(a.mean(),np.mean(~correct[ix][a]) if a.any() else 0,s=20)
  ax.set(title=cohort,xlabel='Coverage',ylabel='Selective risk',xlim=(0,1),ylim=(0,1));ax.legend()
 fig.tight_layout();fig.savefig(OUT/'risk_coverage.png',dpi=200);fig.savefig(OUT/'risk_coverage.pdf');plt.close(fig)
 pd.DataFrame(curves).to_csv(OUT/'risk_coverage.csv',index=False)
 # Explicit analytical sensitivity to the harm of an incorrect click.
 utilities=[]
 for cohort in masks:
  for m in [m for m in metrics if m['cohort']==cohort]:
   if m['policy'] not in ['B','D','E','uniqueness']:continue
   for lam in [0,1,5,10,25]:utilities.append({'cohort':cohort,'policy':m['policy'],'lambda':lam,'utility':(m['accepted']-m['incorrect_accepted']-lam*m['incorrect_accepted'])/m['n']})
 pd.DataFrame(utilities).to_csv(OUT/'utility_sensitivity.csv',index=False)
 # Documented GPT-4o high-detail image sizing; prospective scenario, never billed.
 tokens=[]
 for r in rows:
  w,h=r['width'],r['height'];scale=min(1,2048/max(w,h));w,h=w*scale,h*scale
  scale=min(1,768/min(w,h));w,h=math.floor(w*scale),math.floor(h*scale)
  tokens.append(85+170*math.ceil(w/512)*math.ceil(h/512))
 scenario={'model':'GPT-4o','type':'prospective cost scenario; no LLM calls','pricing_date':'2026-10-23','input_usd_per_million':2.5,'output_usd_per_million':10,'assumed_text_input_tokens_per_case':250,'assumed_output_tokens_per_case':80,'image_tokens_total':sum(tokens),'cases':len(rows),'cost_usd':((sum(tokens)+250*len(rows))*2.5+80*len(rows)*10)/1e6,'same_jev_token_counts_cost_usd':(3199297*2.5+73284*10)/1e6}
 # Qualitative cases are deterministic illustrations, not a random error-rate estimate.
 conditions=[('box_false_accept',lambda i:rows[i]['cohort']=='real' and decisions['B'][0][i] and not correct[i]),('multiple_rejected',lambda i:rows[i]['cohort']=='real' and rows[i]['target_status']=='multiple' and decisions['B'][0][i] and not decisions['D'][0][i]),('absent_rejected',lambda i:rows[i]['cohort']=='real' and rows[i]['target_status']=='absent' and not decisions['E'][0][i] and preds[i]['status']=='ok'),('correct_accept',lambda i:rows[i]['cohort']=='real' and correct[i] and decisions['E'][0][i]),('schema_failure',lambda i:preds[i]['status']!='ok'),('false_rejection',lambda i:rows[i]['cohort']=='real' and correct[i] and not decisions['E'][0][i])]
 examples=[]
 for title,predicate in conditions:
  i=next(i for i in range(len(rows)) if predicate(i));r,p=rows[i],preds[i]
  im=Image.open(ROOT/r['screenshot_path']).convert('RGB');dr=ImageDraw.Draw(im)
  for b in r['ground_truth_boxes']:dr.rectangle(b,outline='#13873c',width=4)
  b=p.get('predicted_box')
  if b and b[2]>b[0] and b[3]>b[1]:dr.rectangle(b,outline='#cf2434',width=4)
  im.thumbnail((520,340));canvas=Image.new('RGB',(560,440),'white');canvas.paste(im,((560-im.width)//2,70));d=ImageDraw.Draw(canvas)
  d.text((10,6),title+' | '+r['case_id'],fill='black');d.text((10,24),r['instruction'][:83],fill='black');d.text((10,42),'Human: '+r['target_status']+' | green=reference; red=prediction',fill='black')
  d.text((10,418),f"B={int(decisions['B'][0][i])} D={int(decisions['D'][0][i])} E={int(decisions['E'][0][i])} | IoU={ov[i]:.3f}",fill='black')
  canvas.save(OUT/(title+'.png'));examples.append({'kind':title,'case_id':r['case_id'],'instruction':r['instruction'],'status':r['target_status'],'iou':float(ov[i]),'error':p.get('error_message'),'image':title+'.png'})
 # Research flow figure, created as vector shapes using matplotlib.
 fig,ax=plt.subplots(figsize=(10,3));ax.axis('off')
 boxes=[(.01,.65,'951 shared cases\n751 real + 200 synthetic'),(.35,.65,'Two blind annotations\n759 status agreements'),(.69,.65,'259 flags -> reviewed B\n692 consensus'),(.69,.08,'Labels frozen\n951 API responses'),(.35,.08,'751 real-only analysis\n200 reuse sensitivity'),(.01,.08,'Frozen policies + offline\nuncertainty / error analysis')]
 for x,y,t in boxes:ax.text(x+.145,y+.12,t,ha='center',va='center',fontsize=10,bbox=dict(boxstyle='round,pad=.6',facecolor='#eef3f8',edgecolor='#315b7e'))
 for x,y,xx,yy in [(.30,.77,.34,.77),(.64,.77,.68,.77),(.835,.57,.835,.40),(.68,.20,.64,.20),(.34,.20,.30,.20)]:ax.annotate('',xy=(xx,yy),xytext=(x,y),arrowprops=dict(arrowstyle='->',color='#315b7e',lw=2))
 ax.set(xlim=(0,1),ylim=(0,1));fig.savefig(OUT/'dataset_flow.png',dpi=200,bbox_inches='tight');fig.savefig(OUT/'dataset_flow.pdf',bbox_inches='tight');plt.close(fig)
 summary={'analysis_type':'post-hoc offline diagnostics; original policies and labels unchanged','exploratory_entropy':exploratory,'bootstrap':'2000 source-image cluster resamples, seed 1729, percentile 95% CIs','zero_error_caveat':'zero-error cluster bootstrap intervals are degenerate; not risk guarantees','cohort_metrics':metrics,'confidence_intervals':cis,'comparisons':comparisons,'calibration':cal,'gpt4o_cost_scenario':scenario,'examples':examples,'real_point_accuracy':{'n':sum(r['cohort']=='real' and r['target_status']=='unique' for r in rows),'correct':sum(r['cohort']=='real' and r['target_status']=='unique' and p.get('status')=='ok' and any(b[0]<=(p['predicted_box'][0]+p['predicted_box'][2])/2<=b[2] and b[1]<=(p['predicted_box'][1]+p['predicted_box'][3])/2<=b[3] for b in r['ground_truth_boxes']) for r,p in zip(rows,preds))},'synthetic_overlap':{'n':len(overlap),'same_image_hash':sum(r['same_image_hash'] for r in overlap),'same_instruction':sum(r['same_instruction'] for r in overlap),'split_counts':pd.Series([r['pilot_split'] for r in overlap]).value_counts().to_dict()}}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'output':str(OUT),'cohorts':{k:int(v.sum()) for k,v in masks.items()},'synthetic_overlap':summary['synthetic_overlap'],'gpt4o_scenario':scenario},indent=2))
if __name__=='__main__':main()
