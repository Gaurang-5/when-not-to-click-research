import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parent))
from paper_content import blocks,ROOT
out=ROOT/'results/extended/math';out.mkdir(exist_ok=True)
for i,x in enumerate(z for z in blocks() if z['kind']=='equation'):
 fig=plt.figure(figsize=(11,0.65));fig.text(.5,.5,'$'+x['tex']+'$',ha='center',va='center',fontsize=14)
 fig.savefig(out/f'equation_{i}.png',dpi=250,bbox_inches='tight',pad_inches=.08);plt.close(fig)
print(out)
