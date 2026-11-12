import numpy as np
from scipy.stats import binomtest

def cluster_bootstrap(rows,statistic,n_boot=1000,seed=1729,group='template_id'):
 groups=sorted({r[group] for r in rows});rng=np.random.default_rng(seed);values=[]
 for _ in range(n_boot):
  draw=rng.choice(groups,len(groups),replace=True);idx=np.concatenate([np.array([i for i,r in enumerate(rows) if r[group]==g]) for g in draw]);v=statistic(idx)
  if v is not None and np.isfinite(v):values.append(v)
 return {'low':float(np.quantile(values,.025)) if values else None,'high':float(np.quantile(values,.975)) if values else None,'defined_replicates':len(values),'requested_replicates':n_boot,'cluster_unit':group,'clusters':len(groups),'method':'percentile_cluster_bootstrap'}

def paired_randomization(rows,difference,n_perm=10000,seed=1729):
 # Cluster sign randomization gives each TEMPLATE one paired unit, rather than iid screenshots.
 groups=sorted({r['template_id'] for r in rows});ds=np.array([np.mean([difference[i] for i,r in enumerate(rows) if r['template_id']==g]) for g in groups]);obs=abs(ds.mean());rng=np.random.default_rng(seed)
 sims=np.abs((rng.choice([-1,1],(n_perm,len(ds)))*ds).mean(axis=1))
 return {'difference':float(ds.mean()),'p_cluster_sign':float((1+(sims>=obs-1e-12).sum())/(n_perm+1)),'clusters':len(groups),'permutations':n_perm}

def holm(ps):
 order=np.argsort(ps);out=np.zeros(len(ps));last=0.
 for rank,i in enumerate(order):last=max(last,min(1.,ps[i]*(len(ps)-rank)));out[i]=last
 return out.tolist()

def iid_zero_error_upper(n,alpha=.05):
 # Only illustration of iid assumption. NOT the reported cluster-aware guarantee.
 return 1-alpha**(1/n) if n else None
