#!/usr/bin/env python3
"""Frozen repeat/prompt study. Resumes without resending paid/schema-failed attempts."""
import argparse,fcntl,hashlib,json,sys,os
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.jev_client import JevClient
class VariantSession(requests.Session):
 def __init__(self,questions):super().__init__();self.questions=questions
 def post(self,url,**kwargs):
  if self.questions:
   for name,instruction in self.questions.items():kwargs['json']['questions'][name]['instructions']=instruction
  return super().post(url,**kwargs)
class StudyClient(JevClient):
 def __init__(self,*a,metadata=None,**kw):self.metadata=metadata;super().__init__(*a,**kw)
 def _log(self,record):
  record.update(self.metadata);record['case_id']=self.metadata['source_case_id'];super()._log(record)

def pending_jobs(protocol,output):
 attempted=set()
 if output.exists():
  for line in output.read_text().splitlines():
   r=json.loads(line)
   if r.get('http_status') not in [401,403]:attempted.add(r['request_id'])
 return [j for j in protocol['jobs'] if j['request_id'] not in attempted]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-live',action='store_true');ap.add_argument('--limit',type=int);args=ap.parse_args()
 path=ROOT/'reports/iteration3/jev_collection_protocol.json';ph=hashlib.sha256(path.read_bytes()).hexdigest()
 if ph!=path.with_suffix('.sha256').read_text().split()[0]:raise SystemExit('Protocol hash mismatch.')
 protocol=json.loads(path.read_text());out=ROOT/'results/iteration3/jev_repeated_calls.jsonl';pending=pending_jobs(protocol,out)
 if args.limit is not None:pending=pending[:args.limit]
 print(json.dumps({'state':'PLAN','total_planned':protocol['new_calls'],'remaining':len(pending),'output':str(out)}),flush=True)
 if not args.execute_live:return
 lock=out.with_suffix('.lock').open('w')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('A collector already owns this log; use only one process.')
 if out.exists():
  for line in out.read_text().splitlines():
   if json.loads(line).get('protocol_sha256')!=ph:raise SystemExit('Prior calls used another protocol.')
 # Refresh under the exclusive lock: another collector may have finished
 # between the initial dry-run plan and successful lock acquisition.
 pending=pending_jobs(protocol,out)
 if args.limit is not None:pending=pending[:args.limit]
 outcomes={}
 for i,job in enumerate(pending,1):
  metadata={'request_id':job['request_id'],'source_case_id':job['case_id'],'variant':job['variant'],'repeat':job['repeat'],'protocol_sha256':ph}
  client=StudyClient(out,metadata=metadata,max_retries=0,session=VariantSession(protocol['prompt_variants'][job['variant']]))
  r=client.predict(job['request_id'],ROOT/job['screenshot_path'],job['instruction']);outcomes[r['status']]=outcomes.get(r['status'],0)+1
  print(json.dumps({'request_id':job['request_id'],'status':r['status'],'progress':f'{i}/{len(pending)}'}),flush=True)
  if r.get('http_status') in [401,403]:print(json.dumps({'state':'STOPPED_AUTH','reason':'Fix TYPESAFE_API_KEY in this terminal; resume same command.'}),flush=True);return
 print(json.dumps({'state':'FINISHED','new_attempts':len(pending),'outcomes':outcomes,'remaining':len(pending_jobs(protocol,out))}),flush=True)
if __name__=='__main__':main()
