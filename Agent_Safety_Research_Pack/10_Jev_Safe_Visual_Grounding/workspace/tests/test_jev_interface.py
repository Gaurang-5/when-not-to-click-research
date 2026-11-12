import copy
import json
import pytest
from PIL import Image
from src.parse_outputs import parse_response, ResponseSchemaError
from src.jev_client import build_payload, JevClient

def fixture():
    return {'model':'jev-1.14.0','answers':{'presence':{'type':'noul','noul':0.8},'uniqueness':{'type':'choice','choice':'one','confidence':0.55,'probabilities':{'none':0.1,'one':0.7,'several':0.2}},'localization':{'type':'box','confidence':0.9,'box':{'left':0.1,'top':0.2,'right':0.4,'bottom':0.6}}},'usage':{'input_tokens':100,'output_tokens':30}}

def test_parse_probability_semantics_and_coordinates():
    out=parse_response(fixture(),1000,500)
    assert out['predicted_box']==[100,100,400,300]
    assert out['uniqueness_confidence']==0.7
    assert out['choice_confidence']==0.55
    assert out['cost_usd']==pytest.approx(0.0000042)

@pytest.mark.parametrize('bad',[None,float('nan'),float('inf'),True,-0.1,1.1,'0.8'])
def test_reject_bad_probability(bad):
    r=fixture();r['answers']['presence']['noul']=bad
    with pytest.raises(ResponseSchemaError):parse_response(r,1000,500)

def test_reject_wrong_version_and_missing_answer():
    r=fixture();r['model']='jev-1.13.0'
    with pytest.raises(ResponseSchemaError):parse_response(r,1000,500)
    r=fixture();del r['answers']['uniqueness']
    with pytest.raises(ResponseSchemaError):parse_response(r,1000,500)

def test_reject_box_and_distribution():
    r=fixture();r['answers']['localization']['box']['right']=0.1
    with pytest.raises(ResponseSchemaError):parse_response(r,1000,500)
    r=fixture();r['answers']['uniqueness']['probabilities']['one']=0.8
    with pytest.raises(ResponseSchemaError):parse_response(r,1000,500)

def test_image_constraints_and_payload(tmp_path):
    path=tmp_path/'image.png';Image.new('RGB',(300,400)).save(path)
    payload,w,h,_=build_payload(path,'Submit')
    assert (w,h)==(300,400)
    assert payload['model']=='jev-1.14.0'
    assert payload['state']['screenshot'] in payload['assets']
    Image.new('RGB',(279,400)).save(path)
    with pytest.raises(ValueError):build_payload(path,'Submit')

def test_missing_credentials(monkeypatch,tmp_path):
    monkeypatch.delenv('TYPESAFE_API_KEY',raising=False)
    with pytest.raises(RuntimeError):JevClient(tmp_path/'log.jsonl')

@pytest.mark.parametrize('bad_key',['abc\u2028def','abc def','abc\ndef'])
def test_reject_malformed_credentials_without_echo(monkeypatch,tmp_path,bad_key):
    monkeypatch.setenv('TYPESAFE_API_KEY',bad_key)
    with pytest.raises(RuntimeError) as exc:
        JevClient(tmp_path/'log.jsonl')
    assert bad_key not in str(exc.value)

def test_mocked_call_logging_and_fail_closed(monkeypatch,tmp_path):
    monkeypatch.setenv('TYPESAFE_API_KEY','test-secret')
    class Response:
        status_code=200
        def json(self):return fixture()
    class Session:
        def post(self,url,**kwargs):
            assert kwargs['headers']['TypeSafe-Danger-Zone-Images']=='true'
            return Response()
    path=tmp_path/'image.png';Image.new('RGB',(300,400)).save(path)
    log=tmp_path/'log.jsonl'
    result=JevClient(log,session=Session()).predict('case',path,'Submit')
    assert result['status']=='ok'
    assert 'test-secret' not in log.read_text()
    assert json.loads(log.read_text())['raw_response']==fixture()
