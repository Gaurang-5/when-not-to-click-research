import pytest
from src.iteration3 import cluster_split, criterion, ranking_metrics, ltt_threshold, parse_baseline

def test_split_keeps_shared_source_and_repeats_exactly():
    rows=[{'case_id':str(i),'source_image':str(i//2)} for i in range(60)]
    a=cluster_split(rows); assert a==cluster_split(rows)
    for i in range(0,60,2):assert a[str(i)]==a[str(i+1)]
    assert set(a.values())=={'fit','calibration','test'}

def test_criterion_separates_point_and_iou_and_preserves_eligibility():
    row={'target_status':'unique','ground_truth_boxes':[[0,0,10,10]]}
    pred={'status':'ok','predicted_box':[4,4,6,6]}
    assert criterion(row,pred,'center')
    assert not criterion(row,pred,'iou03')
    assert not criterion(dict(row,target_status='multiple'),pred,'center')

def test_ranking_ties_are_grouped_not_order_dependent():
    a=ranking_metrics([1,0,1,0],[.9,.9,.2,.2])
    b=ranking_metrics([0,1,0,1],[.9,.9,.2,.2])
    assert a==b and a['auroc']==.5
    assert a['aurc']==.5

def test_ltt_can_abstain_without_claiming_certification():
    x=ltt_threshold([.9]*5,[True]*5,[.8,.9],alpha=.1,delta=.05)
    assert x['threshold'] is None and not x['certified']

def test_ltt_certifies_only_sufficiently_supported_low_risk():
    x=ltt_threshold([.9]*150,[True]*150,[.8,.9],alpha=.1,delta=.05)
    assert x['certified'] and x['accepted']==150

def test_baseline_parser_rejects_geometry_without_repair():
    x={'box':[10,20,30,40],'presence':.8,'one':.7,'confidence':.6,'match_count':'one'}
    assert parse_baseline(x,100,100)['predicted_box']==[10,20,30,40]
    with pytest.raises(ValueError):parse_baseline(dict(x,box=[30,20,10,40]),100,100)

def test_paid_runner_resume_skips_schema_and_timeout_attempts(tmp_path):
    import json
    from scripts.run_iteration3_jev import pending_jobs
    p=tmp_path/'calls.jsonl'
    p.write_text('\n'.join(json.dumps(r) for r in [
        {'request_id':'ok','http_status':200,'status':'ok'},
        {'request_id':'schema','http_status':200,'status':'error'},
        {'request_id':'timeout','status':'error'},
        {'request_id':'auth','http_status':401,'status':'error'}]))
    protocol={'jobs':[{'request_id':x} for x in ['ok','schema','timeout','auth','new']]}
    assert [r['request_id'] for r in pending_jobs(protocol,p)]==['auth','new']

def test_prompt_variant_preserves_question_types(monkeypatch):
    from scripts.run_iteration3_jev import VariantSession
    import requests
    captured={}
    def fake_post(self,url,**kwargs):captured.update(kwargs);return 'sent'
    monkeypatch.setattr(requests.Session,'post',fake_post)
    payload={'questions':{'presence':{'type':'noul','instructions':'old'}}}
    assert VariantSession({'presence':'new'}).post('endpoint',json=payload)=='sent'
    assert captured['json']['questions']['presence']=={'type':'noul','instructions':'new'}

def test_paid_runner_rechecks_log_after_acquiring_lock(tmp_path,monkeypatch):
    """A collector finishing between planning and locking must not cause a resend."""
    import hashlib,json,sys
    from scripts import run_iteration3_jev as runner
    protocol={'new_calls':1,'jobs':[{'request_id':'job','case_id':'case','variant':'original','repeat':2,'screenshot_path':'image.png','instruction':'click'}],'prompt_variants':{'original':{}}}
    path=tmp_path/'reports/iteration3/jev_collection_protocol.json';path.parent.mkdir(parents=True);path.write_text(json.dumps(protocol))
    ph=hashlib.sha256(path.read_bytes()).hexdigest();path.with_suffix('.sha256').write_text(ph)
    out=tmp_path/'results/iteration3/jev_repeated_calls.jsonl';out.parent.mkdir(parents=True)
    def acquired(*args):out.write_text(json.dumps({'request_id':'job','http_status':200,'protocol_sha256':ph})+'\n')
    def no_client(*args,**kwargs):raise AssertionError('A paid request would be duplicated')
    monkeypatch.setattr(runner,'ROOT',tmp_path);monkeypatch.setattr(runner.fcntl,'flock',acquired);monkeypatch.setattr(runner,'StudyClient',no_client);monkeypatch.setattr(sys,'argv',['runner','--execute-live'])
    runner.main()
