"""Explicit API runner; no calls unless --execute-live is passed and credential is present.
Creates raw/parsed append-only call log. Analysis is intentionally separate from demo.
"""
import argparse,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.validate_data import load,validate
from src.jev_client import JevClient

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--execute-live',action='store_true');parser.add_argument('--split',choices=['dev','calibration','test'],default='dev');parser.add_argument('--limit',type=int,default=1);parser.add_argument('--output',type=Path,default=ROOT/'results/live_calls.jsonl');parser.add_argument('--rerun-existing',action='store_true',help='Repeat successful case IDs already present in the output log');args=parser.parse_args()
 if args.limit < 1: parser.error('--limit must be at least 1')
 rows=load(ROOT/'data/pilot_cases.jsonl');validate(rows,ROOT);selected=[r for r in rows if r['split']==args.split][:args.limit]
 if args.split=='test':
  freeze=ROOT/'results/live_frozen_policy.json';digest_file=ROOT/'results/live_frozen_policy.sha256'
  if not freeze.exists() or not digest_file.exists():
   parser.error('test collection requires results/live_frozen_policy.json and its SHA-256 file')
  expected=digest_file.read_text().split()[0]
  actual=hashlib.sha256(freeze.read_bytes()).hexdigest()
  if actual != expected:
   parser.error('frozen live policy hash mismatch; refusing test collection')
  frozen=json.loads(freeze.read_text())
  if frozen.get('test_used_for_selection') is not False or frozen.get('model')!='jev-1.14.0':
   parser.error('invalid live policy freeze; refusing test collection')
 completed=set()
 if args.output.exists() and not args.rerun_existing:
  for line in args.output.read_text().splitlines():
   if line.strip():
    record=json.loads(line)
    if record.get('status')=='ok': completed.add(record.get('case_id'))
 rows=[r for r in selected if r['case_id'] not in completed]
 plan={'split':args.split,'selected_cases':len(selected),'already_successful':len(selected)-len(rows),'planned_calls':len(rows),'output':str(args.output)}
 if not args.execute_live:print(json.dumps({'state':'NOT_RUN',**plan,'reason':'Use --execute-live only after credential configuration and protocol freeze.'}));return
 if not rows: print(json.dumps({'state':'COMPLETE',**plan}));return
 client=JevClient(log_path=args.output)
 outcomes={'ok':0,'error':0}
 for r in rows:
  result=client.predict(r['case_id'],ROOT/r['screenshot_path'],r['instruction']);outcomes[result['status']]=outcomes.get(result['status'],0)+1;print(json.dumps({'case_id':r['case_id'],'status':result['status']}))
 print(json.dumps({'state':'FINISHED',**plan,'outcomes':outcomes}))
if __name__=='__main__':main()
