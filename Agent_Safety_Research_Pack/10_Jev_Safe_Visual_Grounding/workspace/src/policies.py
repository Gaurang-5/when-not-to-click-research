import numpy as np
FIELDS=['presence_confidence','uniqueness_confidence','box_confidence']
def valid_box(p):
 # parse_response already converts normalized in-range edges to pixels using the
 # image dimensions. Policy validity therefore needs ordering/non-negativity,
 # not the synthetic pilot's historical 1000x700 canvas bounds.
 b=p.get('predicted_box');return b is not None and len(b)==4 and all(np.isfinite(v) for v in b) and 0<=b[0]<b[2] and 0<=b[1]<b[3]

def features(preds):
 return np.array([[float(p.get(k)) if p.get(k) is not None else 0. for k in FIELDS] for p in preds])
def score(preds,policy,model=None):
 x=features(preds)
 if policy=='A':s=np.ones(len(preds))
 elif policy=='B':s=x[:,2]
 elif policy=='C':s=np.minimum(x[:,0],x[:,2])
 elif policy=='D':s=x.min(axis=1)
 elif policy=='presence':s=x[:,0]
 elif policy=='uniqueness':s=x[:,1]
 elif policy=='presence_uniqueness':s=x[:,:2].min(axis=1)
 elif policy=='E':s=model.predict_proba(x)[:,1]
 else:raise ValueError(policy)
 required={'A':[], 'B':[2], 'C':[0,2], 'D':[0,1,2], 'E':[0,1,2], 'presence':[0], 'uniqueness':[1], 'presence_uniqueness':[0,1]}[policy]
 for i,p in enumerate(preds):
  if p.get('status')!='ok' or not valid_box(p) or any(p.get(FIELDS[j]) is None or not 0<=p[FIELDS[j]]<=1 for j in required):s[i]=-np.inf
 return s

def decide(preds,scores,threshold):
 accepted=scores>=threshold
 # Clarification uses model prediction only; never ground-truth category.
 actions=['click' if a else 'clarify' if p.get('match_choice') in ['multiple','several'] else 'abstain' for a,p in zip(accepted,preds)]
 return accepted,actions
