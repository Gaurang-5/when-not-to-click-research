"""Pure helpers for exploratory reviewer-requested analyses."""
import hashlib,math
import numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import binom, beta
from .metrics import iou

def cluster_split(rows,seed=1729):
    groups=sorted({r['source_image'] for r in rows},key=lambda x:hashlib.sha256((str(seed)+'|'+x).encode()).hexdigest())
    n=len(groups);split={g:'fit' if i<int(.4*n) else 'calibration' if i<int(.7*n) else 'test' for i,g in enumerate(groups)}
    return {r['case_id']:split[r['source_image']] for r in rows}

def criterion(row,pred,mode='strict'):
    if row['target_status']!='unique' or pred.get('status')!='ok' or not pred.get('predicted_box'):return False
    b=pred['predicted_box'];cx,cy=(b[0]+b[2])/2,(b[1]+b[3])/2
    point=any(g[0]<=cx<=g[2] and g[1]<=cy<=g[3] for g in row['ground_truth_boxes'])
    overlap=max([iou(b,g) for g in row['ground_truth_boxes']]+[0])
    return point if mode=='center' else overlap>=.3 if mode=='iou03' else point and overlap>=.5

def ranking_metrics(y,scores):
    y=np.asarray(y,dtype=bool);s=np.asarray(scores,dtype=float)
    if len(y)==0:return {'auroc':None,'aurc':None,'n':0}
    # AURC is right-continuous threshold risk integrated over observed coverage.
    # Equal scores enter together; there is no arbitrary within-tie ordering.
    order=np.argsort(-s,kind='stable');ss=s[order];yy=y[order]
    ends=np.r_[np.flatnonzero(ss[1:]!=ss[:-1])+1,len(ss)]
    bad=np.cumsum(~yy)[ends-1];cov=ends/len(y);risk=bad/ends
    aurc=float(np.sum(np.diff(np.r_[0,cov])*risk))
    return {'auroc':float(roc_auc_score(y,s)) if len(set(y))==2 else None,'aurc':aurc,'n':len(y)}

def ltt_threshold(scores,correct,grid,alpha=.1,delta=.05):
    s=np.asarray(scores);y=np.asarray(correct,dtype=bool);tests=[];m=len(grid)
    for t in grid:
        a=s>=t;k=int(a.sum());errors=int((a&~y).sum());p=float(binom.cdf(errors,k,alpha)) if k else 1.
        upper=float(beta.ppf(1-delta/m,errors+1,k-errors)) if k>errors else 1.
        tests.append({'threshold':float(t),'accepted':k,'errors':errors,'p_value':p,'simultaneous_upper':upper,'passes':k>0 and p<=delta/m})
    passed=[t for t in tests if t['passes']]
    best=max(passed,key=lambda r:(r['accepted'],r['threshold'])) if passed else {}
    return {'threshold':best.get('threshold'),'accepted':best.get('accepted',0),'certified':bool(passed),'alpha':alpha,'delta':delta,'tests':tests,'method':'one-sided exact binomial LTT with Bonferroni across fixed thresholds; one sampled case per independent source cluster; exploratory dataset'}

def parse_baseline(x,width,height):
    b=x.get('box')
    if not isinstance(b,list) or len(b)!=4 or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in b):raise ValueError('invalid box')
    if not (0<=b[0]<b[2]<=width and 0<=b[1]<b[3]<=height):raise ValueError('out-of-bounds or degenerate box')
    for k in ['presence','one','confidence']:
        v=x.get(k)
        if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or not 0<=v<=1:raise ValueError('invalid prompted confidence')
    if x.get('match_count') not in ['none','one','several']:raise ValueError('invalid match count')
    return {'status':'ok','predicted_box':b,'presence_confidence':x['presence'],'uniqueness_confidence':x['one'],'box_confidence':x['confidence'],'match_choice':x['match_count']}
