"""Render unchanged equations as vector PDF and PNG previews."""
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parent))
from paper_content import blocks,ROOT
from paper_layout import conference_blocks
plt.rcParams.update({'mathtext.fontset':'stix','font.family':'STIXGeneral','pdf.fonttype':42})
out=ROOT/'results/extended/math';out.mkdir(exist_ok=True)
for i,x in enumerate(z for z in conference_blocks(blocks()) if z['kind']=='equation'):
 lines=x['lines'];fig=plt.figure(figsize=(8,max(.48,.35*len(lines))))
 for j,line in enumerate(lines):fig.text(.5,1-(j+.5)/len(lines),'$'+line+'$',ha='center',va='center',fontsize=12)
 fig.savefig(out/f'equation_{i}.png',dpi=250,bbox_inches='tight',pad_inches=.05)
 fig.savefig(out/f'equation_{i}.pdf',bbox_inches='tight',pad_inches=.05);plt.close(fig)
print(out)
