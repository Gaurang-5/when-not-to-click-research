"""Author controlled HTML, render Chrome screenshots, collect DOM labels (not human truth)."""
import json, hashlib, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=['unique','unique','unique','absent','multiple','occluded','offscreen','unclear']
# Structurally different families; no family crosses a split. Shared generator is disclosed.
LAYOUTS=[('sidebar','dev'),('kanban','dev'),('table','calibration'),('dialog','test'),('toolbar','test')]
def main():
 rows=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
  page=browser.new_page(viewport={'width':1000,'height':700},device_scale_factor=1)
  for f,(family,split) in enumerate(LAYOUTS):
   for t in range(5):
    for k,status in enumerate(CATEGORIES):
     cid=f'{family}_{t:02d}_{k:02d}'; label=['Export','Archive','Approve','Publish','Download'][t]
     positions=[(235,180),(55,245),(720,215),(410,355),(730,80)]
     x,y=positions[f]; x+=k*3
     w,h=(12,7) if status=='unclear' else (150,42)
     if status=='offscreen': y=850
     target='' if status=='absent' else f'<button class="target" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{label}</button>'
     if status=='multiple': target+=f'<button class="target" style="left:{x}px;top:{y+110}px;width:150px;height:42px">{label}</button>'
     if family=='sidebar': shell='<aside>Workspace<br><br>Overview<br><br>Documents<br><br>Members</aside><section style="left:220px;top:120px;width:700px;height:450px">Recent documents</section>'
     elif family=='kanban': shell=''.join(f'<section style="left:{40+j*310}px;top:150px;width:280px;height:440px">{title}<p>Project item {t+1}</p></section>' for j,title in enumerate(['To do','In progress','Done']))
     elif family=='table': shell='<table><tr><th>Document</th><th>Owner</th><th>Action</th></tr>'+''.join(f'<tr><td>Report {i+t}</td><td>Demo team</td><td>Review</td></tr>' for i in range(6))+'</table>'
     elif family=='dialog': shell='<div class="veil"></div><section style="left:250px;top:180px;width:500px;height:300px;z-index:2">Confirm document action<p>Review the selected item before continuing.</p></section>'
     else: shell='<section style="left:30px;top:65px;width:940px;height:85px">Document controls</section><section style="left:30px;top:190px;width:940px;height:420px">Document preview<p>Quarterly overview</p></section>'
     overlay=f'<div style="position:absolute;left:{x+65}px;top:{y-5}px;width:115px;height:65px;background:#334155;color:white;z-index:5">Sync status</div>' if status=='occluded' else ''
     html=f'''<!doctype html><html><head><meta charset="utf-8"><style>body{{margin:0;font:17px Arial;background:hsl({205+t*13},25%,96%);color:#192a42;overflow:hidden}}header{{padding:22px;background:#203c60;color:white}}aside{{position:absolute;top:90px;left:0;width:165px;height:580px;background:#dde6ef;padding:20px}}section{{position:absolute;box-sizing:border-box;background:white;border:1px solid #bbc8d8;border-radius:10px;padding:20px}}button{{position:absolute;border:0;border-radius:5px;background:#17647d;color:white;font-size:{'3' if status=='unclear' else '17'}px;z-index:3}}table{{position:absolute;left:50px;top:130px;width:900px;border-collapse:collapse;background:white}}td,th{{border-bottom:1px solid #bbc8d8;padding:22px;text-align:left}}.veil{{position:absolute;inset:70px 0 0;background:#a5b2c7}}</style></head><body><header>Demo {family.title()} · Workspace {t+1}</header>{shell}{target}{overlay}<footer style="position:absolute;bottom:15px;left:30px;color:#5b6575">Synthetic research interface — no real account</footer></body></html>'''
     path=ROOT/'data/html'/f'{cid}.html';path.write_text(html)
     page.goto(path.as_uri()); boxes=page.locator('.target').evaluate_all('(els)=>els.map(e=>{let r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]})')
     shot=ROOT/'data/screenshots'/f'{cid}.png';page.screenshot(path=str(shot))
     visible= status not in ['absent','offscreen']
     row=dict(case_id=cid,application_id=family,template_id=f'{family}_{t:02d}',layout_family=family,screenshot_path=str(shot.relative_to(ROOT)),screenshot_sha256=hashlib.sha256(shot.read_bytes()).hexdigest(),instruction=f'Click {label}.',target_status=status,plausible_match_count=(2 if status=='multiple' else int(visible)),ground_truth_boxes=boxes,localization_eligibility=status=='unique',reference_action='click' if status=='unique' else ('clarify' if status=='multiple' else 'abstain'),difficulty='easy' if status=='unique' else 'hard',source='authored_synthetic_html',source_license='CC0-1.0',annotator_1_label=None,annotator_2_label=None,adjudicated_label=None,procedural_label=status,annotation_status='procedural_unreviewed',split=split,width=1000,height=700,target_size='tiny' if status=='unclear' else 'common',clutter='overlay' if status=='occluded' else 'standard')
     rows.append(row)
  browser.close()
 (ROOT/'data/pilot_cases.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 (ROOT/'data/demo_cases.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows[:8]))
 print(json.dumps({'cases':len(rows),'templates':25,'families':5,'splits':{s:sum(r['split']==s for r in rows) for s in ['dev','calibration','test']}}))
if __name__=='__main__':main()
