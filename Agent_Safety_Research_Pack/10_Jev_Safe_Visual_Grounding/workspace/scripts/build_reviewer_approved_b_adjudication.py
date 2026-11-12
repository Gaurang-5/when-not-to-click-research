#!/usr/bin/env python3
"""Create the final adjudication export using reviewer-approved Annotator B labels."""

import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROUND=ROOT/'data/academic_2000/annotation_round_1'
source=ROUND/'corrected_exports/annotator_b_corrected.json'
comparison=ROUND/'corrected_analysis/case_comparison.csv'
output=ROUND/'reviewer_approved_b_adjudication.json'

with comparison.open(encoding='utf-8') as handle:
    flagged={r['case_id'] for r in csv.DictReader(handle) if r['review_required'].lower()=='true'}
tasks=json.loads(source.read_text(encoding='utf-8'))
by={t['data']['case_id']:t for t in tasks}
if not flagged <= set(by): raise SystemExit('Annotator B export is missing flagged cases')

adjudicated=[]
for case_id in sorted(flagged):
    task=by[case_id]
    active=[a for a in task['annotations'] if not a.get('was_cancelled')]
    if len(active)!=1: raise ValueError(f'{case_id}: expected one active Annotator B annotation')
    result=[]
    existing_notes=[]
    for item in active[0]['result']:
        name=item.get('from_name')
        if name=='target_status':
            copied=dict(item); copied['from_name']='adjudicated_status'; result.append(copied)
        elif name=='target_boxes':
            copied=dict(item); copied['from_name']='adjudicated_boxes'; result.append(copied)
        elif name=='notes':
            existing_notes.extend(item.get('value',{}).get('text',[]))
    note='Reviewer approved Annotator B as the final reference.'
    if existing_notes: note += ' Annotator B note: ' + ' | '.join(existing_notes)
    result.append({'from_name':'adjudication_notes','to_name':'image','type':'textarea',
                   'value':{'text':[note]},'origin':'manual'})
    adjudicated.append({'data':task['data'],'annotations':[{'result':result,'was_cancelled':False}]})

output.write_text(json.dumps(adjudicated,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'state':'REVIEWER_APPROVED_B','cases':len(adjudicated),'output':str(output)}))
