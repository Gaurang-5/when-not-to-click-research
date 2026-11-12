#!/usr/bin/env python3
"""Prepare180 blinded candidate tasks from60 unused ScreenSpot-Pro images."""
import json,hashlib,random,io,sys,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'fresh_real_review';OUT.mkdir(exist_ok=True);(OUT/'images').mkdir(exist_ok=True)
def phash(data):
 im=Image.open(io.BytesIO(data)).convert('RGB');return hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
def main():
 source=json.loads((ROOT/'reports/iteration3/fresh_pro_source.json').read_text());rev=source['revision'];base=f'https://huggingface.co/datasets/likaixin/ScreenSpot-Pro/resolve/{rev}/';rng=random.Random(1729)
 files=[x['path'] for x in source['annotations'] if x['path'].endswith('.json')]
 def fetch(path):
  p=ROOT/'data/academic_2000/source_snapshots'/('pro_'+Path(path).name)
  if not p.exists():
   r=requests.get(base+path,timeout=40);r.raise_for_status();p.write_text(json.dumps(r.json(),indent=2))
  return json.loads(p.read_text())
 with ThreadPoolExecutor(max_workers=4) as ex:groups=list(ex.map(fetch,files))
 # Round-robin across applications, without selecting on model outcomes.
 rng.shuffle(groups)
 for group in groups:rng.shuffle(group)
 pool=[r for level in range(max(map(len,groups))) for group in groups for r in group[level:level+1]]
 existing=[json.loads(x) for x in (ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl').read_text().splitlines() if x.strip()];knownfiles={Path(r['source_image'].split('?d=')[-1]).name for r in existing};seenpixels=set()
 for f in sorted(set(r['source_image'].split('?d=')[-1] for r in existing)):seenpixels.add(phash((ROOT/f).read_bytes()))
 selected=[];seenpaths=set()
 for row in pool:
  path=row['img_filename']
  if path in seenpaths or Path(path).name in knownfiles:continue
  filename=hashlib.sha256(path.encode()).hexdigest()[:16]+'.png';target=OUT/'images'/filename
  if target.exists():data=target.read_bytes()
  else:
   response=requests.get(base+'images/'+path,timeout=60);response.raise_for_status();data=response.content
  px=phash(data)
  if px in seenpixels:continue
  seenpixels.add(px);seenpaths.add(path);target.write_bytes(data);selected.append((row,filename,px,hashlib.sha256(data).hexdigest()))
  print(json.dumps({'new_image':len(selected),'application':row['application']}),flush=True)
  if len(selected)==60:break
 if len(selected)!=60:raise RuntimeError('Not enough disjoint images')
 tasks=[];researcher=[]
 for i,(r,filename,px,sha) in enumerate(selected):
  other=next(x[0] for x in selected[i+1:]+selected[:i] if x[0]['application']!=r['application'])
  for variant,instruction in [('source_positive',r['instruction']),('cross_app_absent_candidate',other['instruction']),('multiple_candidate','click a button')]:
   im=Image.open(OUT/'images'/filename);w,h=im.size;internal={'image':filename,'instruction':instruction,'candidate_type':variant,'source_item':r,'image_sha256':sha,'pixel_sha256':px}
   researcher.append(internal)
 rng.shuffle(researcher)
 for i,r in enumerate(researcher,1):
  cid=f'fresh_review_{i:03}';im=Image.open(OUT/'images'/r['image']);w,h=im.size;r['case_id']=cid
  tasks.append({'data':{'case_id':cid,'instruction':r['instruction'],'image':'/data/local-files/?d=images/'+r['image'],'expected_width':w,'expected_height':h}})
 (OUT/'label_studio_tasks.json').write_text(json.dumps(tasks,indent=2)+'\n');(OUT/'RESEARCHER_ONLY_manifest.json').write_text(json.dumps(researcher,indent=2)+'\n')
 config='''<View><Header value="Instruction shown to agent"/><Text name="instruction" value="$instruction"/><Choices name="target_status" toName="image" choice="single" required="true"><Choice value="unique"/><Choice value="absent"/><Choice value="multiple"/><Choice value="occluded"/><Choice value="offscreen"/><Choice value="unclear"/></Choices><Image name="image" value="$image" zoom="true"/><RectangleLabels name="target_boxes" toName="image"><Label value="valid_target"/></RectangleLabels><TextArea name="notes" toName="image" rows="3" placeholder="Explain uncertainty"/><Choices name="confidence" toName="image" choice="single" required="true"><Choice value="high"/><Choice value="medium"/><Choice value="low"/></Choices></View>'''
 (OUT/'label_config.xml').write_text(config+'\n')
 (OUT/'INSTRUCTIONS.md').write_text('''# Fresh real-interface review:180 tasks,60 unused source screenshots\n\nStatus: CANDIDATES PREPARED, NOT HUMAN LABELED.\n\nUse Label Studio. Import label_studio_tasks.json; paste label_config.xml in Labeling Interface. Enable local-file serving with the document root equal to the fully extracted package folder. The image URLs resolve under images/. Use two separate projects/accounts for two independent annotators and hide all existing annotations.\n\nRead the instruction, inspect visible screenshot pixels, and choose exactly one state: unique, absent, multiple, occluded, offscreen, unclear. Unique: one full clickable box. Multiple: all plausible boxes, at least two. Other states: no boxes. Mark high/medium/low confidence and explain borderline cases. Do not infer invisible/offscreen controls from app knowledge. Use unclear when visual evidence does not support a specific reason. Zoom when necessary; targets may be tiny.\n\nInstructions include original source-positive descriptions, natural descriptions borrowed from another application, and generic button requests. These are candidate construction methods, not true status labels. The generic requests require a judgment of whether multiple plausible matches exist. Reject unrealistic or unresolvable instructions and explain why. Do not force the final status counts to be balanced.\n\nAnnotators receive only images/, tasks, schema and instructions. Keep RESEARCHER_ONLY_manifest.json with authors. After both annotations, export full JSON, compute agreement, adjudicate independently, and freeze labels/analysis before API collection. No model predictions have been collected on these tasks.\n\nSource: likaixin/ScreenSpot-Pro, pinned revision listed in status.json. This is a professional desktop source shift, not a balanced desktop/mobile/web sample. Original high-resolution images are retained; future API resizing must be versioned and box coordinates transformed. Exact file names and decoded image pixels were checked against all951 prior cases and duplicates rejected.\n''')
 (OUT/'status.json').write_text(json.dumps({'state':'CANDIDATES_PREPARED_NOT_ANNOTATED','tasks':len(tasks),'source_images':60,'source':'likaixin/ScreenSpot-Pro','source_revision':rev,'license':'MIT repository claim; privacy/source review before redistribution','source_and_decoded_pixel_disjoint_from_951':True,'candidate_counts':{'source_positive':60,'cross_app_absent_candidate':60,'multiple_candidate':60},'applications':sorted(set(r['source_item']['application'] for r in researcher)),'human_labels_available':False,'model_predictions_collected':False},indent=2)+'\n')
 print(json.dumps({'state':'CANDIDATES_PREPARED_NOT_ANNOTATED','tasks':len(tasks)}),flush=True)
if __name__=='__main__':main()
