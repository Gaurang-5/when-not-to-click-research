import numpy as np
from sklearn.linear_model import LogisticRegression
from .policies import features

def fit_joint(preds,labels):return LogisticRegression(C=1.0,max_iter=1000,random_state=1729).fit(features(preds),labels)
def coverage_threshold(scores,target=.30):
 # Fixed rule: greatest feasible calibration coverage <= target, tie -> largest threshold.
 scores=np.asarray(scores,dtype=float)
 candidates=[np.inf]+sorted(set(float(x) for x in scores if np.isfinite(x)),reverse=True)
 feasible=[(float(np.mean(scores>=t)),t) for t in candidates if np.mean(scores>=t)<=target]
 return max(feasible)[1]
def reliability(scores,labels,bins=10):
 scores=np.asarray(scores); labels=np.asarray(labels);good=np.isfinite(scores);scores=scores[good];labels=labels[good]
 out=[]
 for k in range(bins):
  idx=(scores>=k/bins)&((scores<(k+1)/bins) if k<bins-1 else (scores<=1))
  out.append({'bin':k,'n':int(idx.sum()),'confidence':float(scores[idx].mean()) if idx.any() else None,'frequency':float(labels[idx].mean()) if idx.any() else None})
 return {'n':len(scores),'brier':float(np.mean((scores-labels)**2)) if len(scores) else None,'ece':sum(r['n']*abs(r['confidence']-r['frequency']) for r in out if r['n'])/len(scores) if len(scores) else None,'bins':out}
