import copy
import numpy as np
import pytest
from src.metrics import iou,correctness,summarize
from src.policies import valid_box

def test_policy_box_validity_is_resolution_independent():
 assert valid_box({'predicted_box':[100,200,1400,1500]})
 assert not valid_box({'predicted_box':[100,200,100,1500]})
from src.policies import score,decide
from src.calibration import coverage_threshold,reliability
from src.validate_data import validate,load
from src.statistical_tests import holm,cluster_bootstrap,paired_randomization
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def pred(**kw):return dict({'presence_confidence':.9,'uniqueness_confidence':.8,'box_confidence':.7,'predicted_box':[0,0,10,10],'status':'ok','match_choice':'one'},**kw)
def row(status='unique'):return dict(target_status=status,ground_truth_boxes=[[0,0,10,10]],localization_eligibility=status=='unique',template_id='t')
def test_iou():assert iou([0,0,10,10],[0,0,10,10])==1;assert iou([0,0,1,1],[2,2,3,3])==0;assert iou(None,[0,0,1,1])==0
@pytest.mark.parametrize('status',['absent','multiple','offscreen','occluded','unclear'])
def test_unsafe_category_despite_perfect_box(status):assert not correctness([row(status)],[pred()])[0][0]
def test_unique_match():assert correctness([row()],[pred()])[0][0]
@pytest.mark.parametrize('pol',['A','B','C','D','E','presence','uniqueness','presence_uniqueness'])
def test_error_never_accepted(pol):
 class Model:
  def predict_proba(self,x):return np.tile([.1,.9],(len(x),1))
 s=score([pred(status='error')],pol,Model());assert not decide([pred()],s,0)[0][0]
def test_missing_required():assert np.isneginf(score([pred(presence_confidence=None)],'D')[0]);assert score([pred(presence_confidence=None)],'B')[0]==.7
@pytest.mark.parametrize('box',[[10,0,0,10],[-1,0,10,10],[0,0,float('nan'),10],None])
def test_bad_box(box):assert np.isneginf(score([pred(predicted_box=box)],'A')[0])
def test_gate_values():assert score([pred()],'D')[0]==.7;assert score([pred()],'presence_uniqueness')[0]==.8
@pytest.mark.parametrize('scores',[[.9,.8,.7,.6],[.9,.9,.9,.1],[-np.inf,-np.inf]])
def test_threshold_respects_target(scores):assert np.mean(np.array(scores)>=coverage_threshold(scores,.3))<=.3
def test_zero_accept_not_zero_risk():
 m=summarize([row()],[pred()],[False],['abstain'])
 assert m['selective_risk'] is None
 assert m['marginal_incorrect_action_rate']==0
def test_denominators():
 rs=[row('absent'),row('multiple'),row()];ps=[pred()]*3;m=summarize(rs,ps,[True,False,True],['click','clarify','click']);assert m['selective_risk']==.5;assert m['marginal_incorrect_action_rate']==1/3;assert m['coverage']==2/3;assert m['absent_false_accept_rate']==1;assert m['ambiguous_wrong_accept_rate']==0

def test_perfect_calibration():r=reliability([0,1],[0,1]);assert r['brier']==r['ece']==0

def test_holm():assert holm([.01,.04])==[.02,.04]
def test_cluster_constant():c=cluster_bootstrap([row(),dict(row(),template_id='u')],lambda idx:1.,n_boot=20);assert c['low']==c['high']==1

def test_paired_null():assert paired_randomization([row(),dict(row(),template_id='u')],[0,0],n_perm=20)['p_cluster_sign']==1

def test_dataset():assert validate(load(ROOT/'data/pilot_cases.jsonl'),ROOT)['n']==200
@pytest.mark.parametrize('key',['template_id','application_id','layout_family'])
def test_leakage_rejected(key):
 rs=load(ROOT/'data/pilot_cases.jsonl');a=copy.deepcopy(rs[0]);b=copy.deepcopy(rs[-1]);b[key]=a[key]
 with pytest.raises(AssertionError,match='leakage'):validate([a,b])
def test_image_leakage():
 rs=load(ROOT/'data/pilot_cases.jsonl');a=copy.deepcopy(rs[0]);b=copy.deepcopy(rs[-1]);b['screenshot_sha256']=a['screenshot_sha256']
 with pytest.raises(AssertionError,match='leakage'):validate([a,b])
