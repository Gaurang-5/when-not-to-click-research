import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def render(curves,reliability,table,localization,out):
 fig,ax=plt.subplots(figsize=(7,4))
 for name,pts in curves.items():
  if name in ['A','B','C','D','E']:ax.plot([r['coverage'] for r in pts],[r['risk'] for r in pts],label=name,marker='.',ms=3)
 ax.set(xlabel='Coverage (all test cases)',ylabel='Incorrect / accepted clicks',title='SIMULATED FIXTURE ONLY — risk vs coverage',xlim=(0,1),ylim=(0,1));ax.legend();fig.tight_layout();fig.savefig(out/'risk_coverage.png',dpi=160);plt.close(fig)
 fig,ax=plt.subplots(figsize=(6,4));ax.plot([0,1],[0,1],'k--')
 for name,rel in reliability.items():
  if name in ['presence_all','box_event_all','joint_all']:
   b=[v for v in rel['bins'] if v['n']];ax.plot([v['confidence'] for v in b],[v['frequency'] for v in b],marker='o',label=name)
 ax.set(xlabel='Mean probability / score in equal-width bin',ylabel='Observed frequency',title='SIMULATED FIXTURE ONLY — reliability');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(out/'reliability.png',dpi=160);plt.close(fig)
 fig,ax=plt.subplots(figsize=(7,4));names=[r['policy'] for r in table];ax.bar(names,[r['coverage'] for r in table],label='Coverage');ax.plot(names,[r['selective_risk'] if r['selective_risk'] is not None else float('nan') for r in table],'ro-',label='Incorrect / accepted');ax.set(title='SIMULATED FIXTURE ONLY — policy comparison',ylim=(0,1));ax.tick_params(axis='x',rotation=35);ax.legend();fig.tight_layout();fig.savefig(out/'policy_comparison.png',dpi=160);plt.close(fig)
 fig,ax=plt.subplots(figsize=(6,4));ax.hist(localization,bins=10,range=(0,1));ax.set(title='SIMULATED FIXTURE ONLY — unique-target IoU',xlabel='IoU',ylabel='Unique test cases');fig.tight_layout();fig.savefig(out/'localization.png',dpi=160);plt.close(fig)
