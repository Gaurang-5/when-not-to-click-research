#!/usr/bin/env python3
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.jev_client import build_payload

def main():
 rows=[json.loads(x) for x in (ROOT/'data/academic_2000/annotation_round_1/external_confirmatory/cases.jsonl').read_text().splitlines() if x.strip() and json.loads(x)['case_id'].startswith('ssv2v_')]
 prompt_variants={
 'original':None,
 'literal':{
  'presence':'Using screenshot pixels only, is the requested target visibly available? A hidden, offscreen, or covered control does not count as visible. Instruction: `target_instruction`.',
  'uniqueness':'Count every visible GUI control that could satisfy `target_instruction` in `screenshot`. Select none for zero plausible matches, one for exactly one, several for two or more. Do not choose one arbitrarily when duplicates exist.',
  'localization':'Return the full clickable bounding box of the GUI control matching `target_instruction` in `screenshot`.'},
 'conservative':{
  'presence':'Check whether the screenshot itself contains a visible control that fulfills `target_instruction`. Do not rely on what this application usually contains or what scrolling might reveal.',
  'uniqueness':'Assess whether `target_instruction` identifies no visible control, exactly one visible control, or several plausible visible controls in `screenshot`. If multiple alternatives fit, select several; use only visible evidence.',
  'localization':'Locate the full clickable GUI element described by `target_instruction` in `screenshot`, with edges around the clickable control rather than only its text.'}}
 jobs=[]
 for variant,repeats in [('original',range(2,6)),('literal',[1]),('conservative',[1])]:
  for repeat in repeats:
   for r in rows:jobs.append({'request_id':f"{variant}:r{repeat}:{r['case_id']}",'case_id':r['case_id'],'variant':variant,'repeat':repeat,'screenshot_path':r['screenshot_path'],'instruction':r['instruction']})
 protocol={'version':'reviewer-iteration3-v1','model':'jev-1.14.0','real_cases':len(rows),'new_calls':len(jobs),'existing_original_pass':'results/external_confirmatory_calls.jsonl','prompt_variants':prompt_variants,'jobs':jobs,'retry_policy':'skip attempted non-auth request IDs, including timeout/schema errors; stop at auth failure; no automatic retries','analysis_status':'exploratory, prompts fixed before new collection'}
 out=ROOT/'reports/iteration3/jev_collection_protocol.json';encoded=json.dumps(protocol,indent=2)+'\n'
 if out.exists() and out.read_text()!=encoded:raise SystemExit('Existing protocol differs; preserve it and version any change.')
 out.write_text(encoded);out.with_suffix('.sha256').write_text(hashlib.sha256(encoded.encode()).hexdigest()+'  '+out.name+'\n')
 print(json.dumps({'state':'PREPARED','cases':len(rows),'new_calls':len(jobs),'protocol':str(out)}))
if __name__=='__main__':main()
