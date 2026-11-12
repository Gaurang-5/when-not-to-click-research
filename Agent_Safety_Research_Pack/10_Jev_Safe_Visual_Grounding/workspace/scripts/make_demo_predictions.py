"""Unit/integration fixture generator. LABEL-CONDITIONED SIMULATION, never model output."""
import sys,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.validate_data import load

def main():
 rng=np.random.default_rng(1729);out=[]
 for i,r in enumerate(load(ROOT/'data/pilot_cases.jsonl')):
  status=r['target_status'];visible=status not in ['absent','offscreen'];unique=status not in ['multiple','absent','offscreen']
  # Broad overlapping distributions are solely arbitrary software test fixtures.
  presence=float(rng.beta(4 if visible else 2,2 if visible else 4));uni=float(rng.beta(4 if unique else 2,2 if unique else 4));boxscore=float(rng.beta(4,2))
  box=list(r['ground_truth_boxes'][0]) if r['ground_truth_boxes'] and status!='offscreen' else [400.,250.,550.,292.]
  if rng.random()<.25:box=[box[0]+80,box[1]+50,box[2]+80,box[3]+50]
  out.append(dict(case_id=r['case_id'],model_name='SIMULATED_FIXTURE_NOT_JEV',model_version='fixture_v1',provenance='simulated_fixture',presence_confidence=presence,uniqueness_confidence=uni,box_confidence=boxscore,predicted_box=box,status='error' if i%37==0 else 'ok',match_choice='multiple' if uni<.4 else 'one',latency_ms=None,calls=0,cost_usd=None,error_message='intentional fixture error' if i%37==0 else None))
 (ROOT/'data/demo_predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in out));print({'simulated_rows':len(out),'real_api_calls':0})
if __name__=='__main__':main()
