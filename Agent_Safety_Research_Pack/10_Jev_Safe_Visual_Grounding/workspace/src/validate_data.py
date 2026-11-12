import json,hashlib
from pathlib import Path
STATUSES={'unique','absent','multiple','occluded','offscreen','unclear'}
def load(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def validate(rows,root=None):
 seen=set(); hashes={}; groups={}
 for r in rows:
  assert r['case_id'] not in seen,'duplicate case';seen.add(r['case_id'])
  assert r['target_status'] in STATUSES,'unknown category'
  assert r['split'] in {'dev','calibration','test'}
  assert r['localization_eligibility']==(r['target_status']=='unique')
  assert r['reference_action']==('click' if r['target_status']=='unique' else 'clarify' if r['target_status']=='multiple' else 'abstain')
  assert r['plausible_match_count']>=0
  for b in r['ground_truth_boxes']:assert len(b)==4 and b[0]<b[2] and b[1]<b[3]
  for key in ['template_id','layout_family','application_id']:
   group=(key,r[key]); assert groups.get(group,r['split'])==r['split'],f'{key} leakage';groups[group]=r['split']
  h=r['screenshot_sha256'];assert hashes.get(h,r['split'])==r['split'],'image leakage';hashes[h]=r['split']
  if root:
   p=Path(root)/r['screenshot_path'];assert p.is_file();assert hashlib.sha256(p.read_bytes()).hexdigest()==h
 return {'n':len(rows),'templates':len({r['template_id'] for r in rows})}
