#!/usr/bin/env python3
"""Build a disjoint-source candidate cohort for HUMAN review, never automatic truth."""
import sys,json,io,hashlib,random,zipfile,re,csv
from pathlib import Path
from urllib.parse import unquote
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'fresh_real_review';OUT.mkdir(exist_ok=True);(OUT/'images').mkdir(exist_ok=True)
class RangeReader(io.RawIOBase):
 def __init__(self,url):
  self.url=url;self.pos=0;self.session=requests.Session();r=self.session.get(url,headers={'Range':'bytes=-65536'},timeout=60);r.raise_for_status()
  m=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',r.headers.get('Content-Range',''))
  if r.status_code!=206 or not m:raise ValueError('Server did not return a bounded range')
  self.size=int(m[3]);self.cache={(int(m[1]),int(m[2])+1):r.content}
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,offset,whence=0):
  self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset;return self.pos
 def read(self,n=-1):
  end=self.size if n<0 else min(self.size,self.pos+n)
  if end<=self.pos:return b''
  start=self.pos
  for (a,b),data in self.cache.items():
   if a<=start and end<=b:self.pos=end;return data[start-a:end-a]
  url=self.url+f'?download=true&range_start={start}&range_end={end-1}'
  r=self.session.get(url,headers={'Range':f'bytes={start}-{end-1}'},timeout=90);r.raise_for_status()
  expected=f'bytes {start}-{end-1}/{self.size}'
  if r.status_code!=206 or r.headers.get('Content-Range')!=expected or len(r.content)!=end-start:raise ValueError('Unexpected range response; refusing corrupted archive bytes')
  self.cache[(start,end)]=r.content;self.pos=end;return r.content

def pixelhash(path_or_bytes):
 im=Image.open(io.BytesIO(path_or_bytes) if isinstance(path_or_bytes,bytes) else path_or_bytes).convert('RGB')
 return hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
def main():
 revision=json.loads((ROOT/'reports/iteration3/fresh_source_revision.json').read_text())['revision'];url=f'https://huggingface.co/datasets/OS-Copilot/ScreenSpot-v2/resolve/{revision}/screenspotv2_image.zip'
 existing=[json.loads(x) for x in (ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl').read_text().splitlines() if x.strip()]
 knownfiles={Path(r['source_image'].split('?d=')[-1]).name for r in existing};knownpixels=set()
 for source in sorted(set(r['source_image'].split('?d=')[-1] for r in existing)):
  knownpixels.add(pixelhash(ROOT/source))
 archive=zipfile.ZipFile(RangeReader(url));entries={Path(x.filename).name:x for x in archive.infolist() if not x.is_dir() and '/__MACOSX/' not in x.filename and not Path(x.filename).name.startswith('._')}
 selected=[];rng=random.Random(1729);tasks=[];mapping=[]
 for platform in ['desktop','mobile','web']:
  records=json.loads((ROOT/f'data/academic_2000/source_snapshots/original_ssv2_{platform}.json').read_text());rng.shuffle(records);count=0
  for source in records:
   name=source['img_filename']
   if name in knownfiles or name not in entries:continue
   target=OUT/'images'/name
   if target.exists():data=target.read_bytes()
   else:data=archive.read(entries[name])
   ph=pixelhash(data)
   if ph in knownpixels:continue
   knownpixels.add(ph);target.write_bytes(data);count+=1;imageid=f'fresh_{platform}_{count:03}';sourcebox=source['bbox'];im=Image.open(io.BytesIO(data));w,h=im.size
   for variant,instruction in [('positive',source['instruction']),('absent_candidate','open the quantum synchronization settings'),('multiple_candidate','click a button')]:
    cid=imageid+'_'+variant;tasks.append({'data':{'case_id':cid,'instruction':instruction,'image':'/data/local-files/?d=images/'+name,'expected_width':w,'expected_height':h}})
    mapping.append({'case_id':cid,'candidate_type':variant,'platform':platform,'source_image':name,'image_sha256':hashlib.sha256(data).hexdigest(),'pixel_sha256':ph,'source_instruction':source['instruction'],'source_bbox_xywh':sourcebox,'source_repository':'OS-Copilot/ScreenSpot-v2','source_revision':revision,'human_status':'UNLABELED','source_public_label_only':variant=='positive'})
   print(json.dumps({'downloaded_new_image':imageid,'platform_count':count}),flush=True)
   if count==20:break
  if count<20:raise ValueError(f'Only {count} disjoint images for {platform}')
 (OUT/'label_studio_tasks.json').write_text(json.dumps(tasks,indent=2)+'\n');(OUT/'RESEARCHER_ONLY_manifest.json').write_text(json.dumps(mapping,indent=2)+'\n')
 # Keep exactly the already-tested labeling schema; no preannotations or model scores.
 configs=list((ROOT/'annotation_tools').rglob('config.xml'))
 if configs:(OUT/'label_config.xml').write_text(configs[0].read_text())
 (OUT/'INSTRUCTIONS.md').write_text('''# Fresh real-interface candidate cohort: HUMAN LABELS REQUIRED\n\n180 tasks on60 previously unused source screenshots:20 desktop,20 mobile,20 web. Each image has a source-positive instruction and two counterfactual instructions. The proposed balance is not ground truth. Do not force one-third per status; report what is visibly present and whether the instruction is unique.\n\nImport label_studio_tasks.json, use label_config.xml, enable local-files serving with document root equal to this extracted folder, and configure local image storage. Use two independent annotators. Do not distribute RESEARCHER_ONLY_manifest.json to annotators.\n\nChoose unique/absent/multiple/occluded/offscreen/unclear, draw full valid target boxes for unique/multiple, record confidence and uncertainty notes. Human review may reject unrealistic counterfactual instructions. The generic multiple instruction and artificial absent phrase require realism assessment; they are controlled probes, not natural user-query samples. Source-positive instructions can also be ambiguous. Never treat candidate_type as a human label.\n\nThe image file names and exact decoded pixels were compared with the current951 cases; direct duplicates were rejected. This is an unused-source candidate pool, not a completed fresh confirmatory benchmark. Freeze final labels and a prespecified analysis before collecting Jev/model predictions. Do not tune prompts using the new screenshots.\n''')
 (OUT/'status.json').write_text(json.dumps({'state':'CANDIDATES_PREPARED_NOT_ANNOTATED','cases':len(tasks),'source_images':60,'platforms':{'desktop':20,'mobile':20,'web':20},'duplicate_source_and_pixel_check':True,'label_status':'human review required','source_revision':revision},indent=2)+'\n')
 print(json.dumps({'state':'CANDIDATES_PREPARED_NOT_ANNOTATED','tasks':len(tasks)}),flush=True)
if __name__=='__main__':main()
