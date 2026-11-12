#!/usr/bin/env python3
"""Serial, resumable same-input Qwen baseline; no cloud API or billing."""
import argparse,base64,datetime,fcntl,hashlib,json,sys,time
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.iteration3 import parse_baseline

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-local',action='store_true');ap.add_argument('--limit',type=int);args=ap.parse_args()
 protocol_path=ROOT/'reports/iteration3/baseline_protocol.json';protocol=json.loads(protocol_path.read_text());ph=hashlib.sha256(protocol_path.read_bytes()).hexdigest()
 rows=[json.loads(x) for x in (ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl').read_text().splitlines() if x.strip()]
 out=ROOT/'results/iteration3/qwen_baseline_calls.jsonl';out.parent.mkdir(exist_ok=True)
 completed=set()
 if out.exists():
  for line in out.read_text().splitlines():
   r=json.loads(line)
   if r.get('protocol_sha256')!=ph:raise SystemExit('Existing log uses another protocol. Create a new experiment version.')
   completed.add(r['case_id'])
 pending=[r for r in rows if r['case_id'] not in completed]
 if args.limit:pending=pending[:args.limit]
 print(json.dumps({'state':'PLAN','cases':len(rows),'attempted':len(completed),'pending':len(pending),'protocol_sha256':ph}),flush=True)
 if not args.execute_local:return
 lock=out.with_suffix('.lock').open('w')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('Another baseline collector is active.')
 version=requests.get('http://localhost:11434/api/version',timeout=10).json()
 tags=requests.get('http://localhost:11434/api/tags',timeout=10).json();tag=next((t for t in tags['models'] if t['name']==protocol['model']),None)
 if tag is None:raise SystemExit('Pinned local model is not downloaded.')
 metadata={'ollama':version,'model':tag,'machine':'Apple arm64, 18GiB unified memory','protocol_sha256':ph,'collection_mode':'serial local HTTP, cold first request retained'}
 meta=ROOT/'results/iteration3/qwen_environment.json'
 if meta.exists() and json.loads(meta.read_text())['model']['digest']!=tag['digest']:raise SystemExit('Local model digest changed.')
 meta.write_text(json.dumps(metadata,indent=2)+'\n')
 schema={'type':'object','properties':{'box':{'type':'array','items':{'type':'number'},'minItems':4,'maxItems':4},'presence':{'type':'number','minimum':0,'maximum':1},'one':{'type':'number','minimum':0,'maximum':1},'confidence':{'type':'number','minimum':0,'maximum':1},'match_count':{'type':'string','enum':['none','one','several']}},'required':['box','presence','one','confidence','match_count']}
 errors=0
 for index,row in enumerate(pending,1):
  image=(ROOT/row['screenshot_path']).read_bytes();start=time.monotonic()
  record={'case_id':row['case_id'],'model':protocol['model'],'model_digest':tag['digest'],'protocol_sha256':ph,'image_sha256':hashlib.sha256(image).hexdigest(),'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'error','cost_usd':None,'cost_note':'local compute and energy unpriced; no API charge'}
  payload={'model':protocol['model'],'prompt':protocol['prompt']+f"\nImage dimensions: {row['width']} x {row['height']}.\nInstruction: "+row['instruction'],'images':[base64.b64encode(image).decode()],'format':schema,'stream':False,'keep_alive':'10m','options':{k:protocol[k] for k in ['temperature','seed','num_ctx','num_predict']}}
  try:
   response=requests.post('http://localhost:11434/api/generate',json=payload,timeout=180);record['http_status']=response.status_code;raw=response.json();record['raw_response']=raw
   if response.status_code!=200:raise ValueError('local inference HTTP error')
   if not raw.get('done') or raw.get('done_reason')=='length':raise ValueError('incomplete or token-limited output')
   record.update(parse_baseline(json.loads(raw['response']),row['width'],row['height']))
  except (requests.RequestException,ValueError,KeyError,TypeError) as exc:record['error_message']=str(exc)[:300]
  record['latency_ms']=(time.monotonic()-start)*1000
  with out.open('a') as f:f.write(json.dumps(record,allow_nan=False)+'\n')
  print(json.dumps({'case_id':row['case_id'],'status':record['status'],'seconds':round(record['latency_ms']/1000,2),'progress':f'{len(completed)+index}/{len(rows)}'}),flush=True)
  errors=errors+1 if record.get('http_status')!=200 else 0
  if errors>=3:print('STOPPED: three consecutive runtime failures. Existing records preserved.',flush=True);return
 print(json.dumps({'state':'FINISHED','new_attempts':len(pending),'log':str(out)}),flush=True)
if __name__=='__main__':main()
