#!/usr/bin/env python3
"""Resumable Jev collection for the frozen external confirmatory cohort."""

import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.jev_client import JevClient

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--execute-live',action='store_true')
    ap.add_argument('--manifest',type=Path,default=ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl')
    ap.add_argument('--output',type=Path,default=ROOT/'results/external_confirmatory_calls.jsonl')
    ap.add_argument('--limit',type=int)
    args=ap.parse_args()
    if not args.manifest.exists(): raise SystemExit('External manifest missing; run prepare_external_confirmatory.py after label freeze.')
    rows=[json.loads(x) for x in args.manifest.read_text().splitlines() if x.strip()]
    completed=set()
    if args.output.exists():
        for line in args.output.read_text().splitlines():
            r=json.loads(line); completed.add(r['case_id']) if r.get('status')=='ok' else None
    pending=[r for r in rows if r['case_id'] not in completed]
    if args.limit is not None: pending=pending[:args.limit]
    plan={'total_cases':len(rows),'already_successful':len(completed & {r['case_id'] for r in rows}),
          'planned_calls':len(pending),'output':str(args.output)}
    if not args.execute_live:
        print(json.dumps({'state':'NOT_RUN',**plan,'reason':'Dry run. Add --execute-live only after final label freeze and credential configuration.'})); return
    client=JevClient(args.output)
    outcomes={'ok':0,'error':0}
    for row in pending:
        result=client.predict(row['case_id'],ROOT/row['screenshot_path'],row['instruction'])
        outcomes[result['status']]=outcomes.get(result['status'],0)+1
        print(json.dumps({'case_id':row['case_id'],'status':result['status']}))
        if result.get('http_status') in (401,403):
            print(json.dumps({'state':'STOPPED_AUTHENTICATION_ERROR',**plan,
                              'outcomes':outcomes,
                              'reason':'The server rejected the API key. Replace TYPESAFE_API_KEY and retry with --limit 1.'}))
            return
    print(json.dumps({'state':'FINISHED',**plan,'outcomes':outcomes}))
if __name__=='__main__': main()
