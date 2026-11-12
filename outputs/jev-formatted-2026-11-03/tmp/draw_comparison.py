from pathlib import Path
import json,html
root=Path(__file__).resolve().parent
src=Path('/Users/gaurangbhatia/research/Agent_Safety_Research_Pack/10_Jev_Safe_Visual_Grounding/workspace/results/iteration3/collection_summary.json')
d=json.loads(src.read_text())['baseline']['paired_geometry_comparison']
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="800" viewBox="0 0 1600 800"><rect width="1600" height="800" fill="white"/>']
def text(x,y,t,size=24,fill='#222',weight='normal',anchor='start'):
 s.append(f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(t)}</text>')
def line(x1,y1,x2,y2,color='#ccd0d6',width=1):s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')
def rect(x,y,w,h,fill):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
text(55,48,'Localization on 131 unique real-interface targets',32,'#191877','bold')
text(55,86,'Matched inputs and human references; frozen model configurations',23,'#555')
text(230,151,'Accuracy (%)',25,weight='bold');text(1030,151,'Qwen − Jev (percentage points)',25,weight='bold')
rect(230,174,28,16,'#242477');text(270,190,'Jev',22);rect(365,174,28,16,'#7899ba');text(405,190,'Quantized Qwen',22)
for v in range(0,71,10):
 x=230+v*8;line(x,218,x,658);text(x,690,str(v),21,anchor='middle')
for v in range(-35,6,5):
 x=1015+(v+35)*11;line(x,218,x,658,'#888' if v==0 else '#e5e5e5',2 if v==0 else 1);text(x,690,str(v),21,anchor='middle')
for label,counts,key,y in [('Strict',(41,22),'strict',275),('IoU ≥ 0.3',(64,34),'iou03',425),('Centre only',(77,67),'center',575)]:
 text(55,y+13,label,25,weight='bold')
 for idx,c in enumerate(counts):
  pct=c/131*100;yy=y-35+idx*44;rect(230,yy,pct*8,31,['#242477','#7899ba'][idx]);text(238+pct*8,yy+24,f'{pct:.1f}',23)
 k=key+'_unique_accuracy_difference_Qwen_minus_Jev';point=d['estimates'][k]*100;ci=d['source_cluster_ci'][k];lo=ci['low']*100;hi=ci['high']*100
 X=lambda v:1015+(v+35)*11
 line(X(lo),y,X(hi),y,'#242477',4);line(X(lo),y-10,X(lo),y+10,'#242477',3);line(X(hi),y-10,X(hi),y+10,'#242477',3)
 s.append(f'<circle cx="{X(point)}" cy="{y}" r="7" fill="#242477"/>');text(1230,y+43,f'{point:.1f} [{lo:.1f}, {hi:.1f}]',23,anchor='middle')
text(55,746,'Intervals: paired 95% source-cluster bootstrap intervals (2,000 resamples).',23)
text(55,781,'Exploratory endpoints; these comparisons do not establish general model superiority.',22,'#555')
s.append('</svg>');(root/'figure7.svg').write_text('\n'.join(s))
