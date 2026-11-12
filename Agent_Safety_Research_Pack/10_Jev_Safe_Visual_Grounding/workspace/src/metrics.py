import numpy as np

def iou(a,b):
 if a is None or b is None:return 0.
 inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
 union=max(0,a[2]-a[0])*max(0,a[3]-a[1])+max(0,b[2]-b[0])*max(0,b[3]-b[1])-inter
 return inter/union if union>0 else 0.
def correctness(rows,preds):
 overlaps=np.array([max([iou(p.get('predicted_box'),b) for b in r['ground_truth_boxes']]+[0.]) for r,p in zip(rows,preds)])
 eligible=np.array([r['localization_eligibility'] for r in rows])
 # Primary criterion BOTH IoU>=.5 and predicted-center inside target, unique visible eligibility.
 centers=[]
 for r,p in zip(rows,preds):
  b=p.get('predicted_box');center=((b[0]+b[2])/2,(b[1]+b[3])/2) if b else (-1,-1)
  centers.append(any(g[0]<=center[0]<=g[2] and g[1]<=center[1]<=g[3] for g in r['ground_truth_boxes']))
 return eligible & (overlaps>=.5) & centers,overlaps

def ratio(n,d):return float(n/d) if d else None

def summarize(rows,preds,accepted,actions):
 correct,overlap=correctness(rows,preds); accepted=np.asarray(accepted,dtype=bool);n=len(rows);k=int(accepted.sum());bad=int((accepted&~correct).sum())
 status=np.array([r['target_status'] for r in rows]);unique=status=='unique';absent=status=='absent';amb=status=='multiple'
 useful=accepted&correct&unique
 return {'n':n,'accepted':k,'incorrect_accepted':bad,'coverage':ratio(k,n),
         'selective_risk':ratio(bad,k),
         'marginal_incorrect_action_rate':ratio(bad,n),
         'absent_n':int(absent.sum()),'absent_false_accepts':int((accepted&absent).sum()),'absent_false_accept_rate':ratio((accepted&absent).sum(),absent.sum()),'ambiguous_n':int(amb.sum()),'ambiguous_wrong_accepts':int((accepted&amb).sum()),'ambiguous_wrong_accept_rate':ratio((accepted&amb).sum(),amb.sum()),'abstention_rate':ratio(actions.count('abstain'),n),'clarification_rate':ratio(actions.count('clarify'),n),'unique_n':int(unique.sum()),'unique_correct_accepted':int(useful.sum()),'unique_useful_automation_rate':ratio(useful.sum(),unique.sum()),'useful_automation_all_cases':ratio(useful.sum(),n),'unique_localization_acc_05':ratio(((overlap>=.5)&unique).sum(),unique.sum()),'unique_localization_acc_075':ratio(((overlap>=.75)&unique).sum(),unique.sum()),'unique_mean_iou':float(overlap[unique].mean()) if unique.any() else None,'api_error_n':sum(p.get('status')!='ok' for p in preds)}

def risk_curve(rows,preds,scores):
 correct,_=correctness(rows,preds);out=[]
 for threshold in sorted(set(float(x) for x in scores if np.isfinite(x)),reverse=True):
  a=scores>=threshold;out.append({'threshold':threshold,'coverage':float(a.mean()),'risk':float((a&~correct).sum()/a.sum())})
 return out
