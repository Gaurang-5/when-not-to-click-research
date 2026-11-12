"""Plot completed, same-input geometry and paired source-cluster intervals."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'results/iteration3/collection_summary.json').read_text())['baseline']
if s['state']!='COMPLETE':raise SystemExit('Complete baseline required; partial results are not plotted.')
names=['strict','iou03','center'];labels=['Strict','IoU >= 0.3','Center in box'];metrics=s['primary_metrics'];n=metrics['Jev']['unique_n']
fig,axes=plt.subplots(1,2,figsize=(10.6,3.7),gridspec_kw={'width_ratios':[1.15,1]})
x=np.arange(3);w=.35
for model,offset,color in [('Jev',-w/2,'#16324a'),('Qwen',w/2,'#2f7d74')]:
 counts=[metrics[model][mode+'_correct'] for mode in names];bars=axes[0].bar(x+offset,np.array(counts)/n*100,w,label=model,color=color)
 for bar,count in zip(bars,counts):axes[0].text(bar.get_x()+w/2,bar.get_height()+1.4,f'{count}/{n}',ha='center',fontsize=8)
axes[0].set_xticks(x,labels);axes[0].set_ylabel('Unique-target localization accuracy (%)');axes[0].set_ylim(0,72);axes[0].legend(frameon=False);axes[0].set_title('Same real inputs; fixed human labels',fontsize=11)
paired=s['paired_geometry_comparison'];point=[];lo=[];hi=[]
for mode in names:
 key=mode+'_unique_accuracy_difference_Qwen_minus_Jev';point.append(paired['estimates'][key]*100);ci=paired['source_cluster_ci'][key];lo.append(ci['low']*100);hi.append(ci['high']*100)
point=np.array(point);axes[1].errorbar(point,x,xerr=np.array([point-np.array(lo),np.array(hi)-point]),fmt='o',capsize=4,color='#16324a')
axes[1].axvline(0,color='#64748b',ls='--',lw=1);axes[1].set_yticks(x,labels);axes[1].invert_yaxis();axes[1].set_xlabel('Qwen minus Jev (percentage points)');axes[1].set_title('Paired 95% source-cluster intervals',fontsize=11)
for ax in axes:
 ax.spines[['top','right']].set_visible(False);ax.grid(axis='x' if ax is axes[1] else 'y',alpha=.15);ax.set_axisbelow(True)
fig.tight_layout();out=ROOT/'results/iteration3/same_data_comparison.png';fig.savefig(out,dpi=250,bbox_inches='tight');plt.close(fig);print(out)
