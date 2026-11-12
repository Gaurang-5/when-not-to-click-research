#!/usr/bin/env python3
"""Prepare a reproducible blinded human-review queue; does not claim review."""
import sys,json,csv,random,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.extended_analysis import load
OUT=ROOT/'reviewer_audit';OUT.mkdir(exist_ok=True);(OUT/'images').mkdir(exist_ok=True)
rows,_=load();flagged=[r for r in rows if r['label_provenance']=='reviewer_approved_annotator_b'];rng=random.Random(1729);chosen=[]
for state in sorted(set(r['target_status'] for r in flagged)):
 group=[r for r in flagged if r['target_status']==state];chosen+=rng.sample(group,min(10,len(group)))
chosen+=rng.sample([r for r in flagged if r not in chosen],60-len(chosen));chosen+=rng.sample([r for r in rows if r['label_provenance']=='two_annotator_consensus'],40);rng.shuffle(chosen)
fields=['review_id','image','instruction','target_status','boxes_xyxy','confidence','notes']
with (OUT/'blind_review.csv').open('w') as f:
 w=csv.DictWriter(f,fields);w.writeheader()
 for i,r in enumerate(chosen,1):
  name=f'audit_{i:03}.jpg';shutil.copy2(ROOT/r['screenshot_path'],OUT/'images'/name)
  w.writerow(dict(review_id=f'audit_{i:03}',image='images/'+name,instruction=r['instruction']))
with (OUT/'RESEARCHER_ONLY_mapping.csv').open('w') as f:
 w=csv.DictWriter(f,['review_id','case_id','sampling_group']);w.writeheader();w.writerows(dict(review_id=f'audit_{i:03}',case_id=r['case_id'],sampling_group='flagged' if r['label_provenance']=='reviewer_approved_annotator_b' else 'consensus') for i,r in enumerate(chosen,1))
(OUT/'REVIEWER_INSTRUCTIONS.md').write_text('''# Blinded audit: 100 cases: 60 flagged and 40 consensus\n\nStatus: PREPARED, NOT REVIEWED.\n\nGive the reviewer only blind_review.csv, images/, and this instruction file. Keep RESEARCHER_ONLY_mapping.csv with the study authors. No model scores or previous labels are supplied.\n\nFor each instruction, inspect only the visible screenshot. Choose exactly one status: unique, absent, multiple, occluded, offscreen, or unclear. Draw all full clickable target boxes only for unique/multiple, as absolute [left, top, right, bottom] pixels in the supplied image. Unique requires exactly one box; multiple requires at least two. Do not infer absent versus offscreen from app knowledge. If pixels cannot distinguish the reason, use unclear and explain. Record high/medium/low confidence and a short reason for borderline cases.\n\nReturn the completed CSV. Do not see the previous annotators' answers or model outputs before completing the pass. Do not overwrite the frozen dataset. Authors compare after review and version any changes.\n\nSampling: seed 1729, stratified across final target states, then filled randomly to 60 among the 259 flagged cases. This oversamples rare states and is not an unweighted representative error-rate sample. Forty consensus cases are sampled independently and randomly to check agreement cases as well. Do not claim kappa or independent adjudication until completed human responses are available.\n''')
print('Prepared 100 blinded review tasks; no human audit performed.')
