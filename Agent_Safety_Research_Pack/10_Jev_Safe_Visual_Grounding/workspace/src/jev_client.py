"""Pinned experimental TypeSafe image API client. No live calls on import.
Only TYPESAFE_API_KEY is read; keys and request headers are never logged.
Cost is a list-price estimate, not an invoice. Retries default to zero to avoid
silent duplicate billing; every attempted response is separately logged.
"""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid
import requests
from PIL import Image
from .parse_outputs import parse_response, ResponseSchemaError

ENDPOINT = 'https://api.typesafe.ai/v1/systemone'
MODEL = 'jev-1.14.0'
PROMPT_VERSION = 'presence-count-box-v1'

def build_payload(image_path, instruction, model=MODEL):
    if not isinstance(instruction,str) or not instruction.strip():
        raise ValueError('instruction must be nonempty text')
    if model != MODEL:
        raise ValueError('this experiment is pinned to jev-1.14.0')
    path=Path(image_path)
    data=path.read_bytes()
    if len(data)>16*1024*1024: raise ValueError('image exceeds 16 MiB')
    with Image.open(path) as im:
        if im.format not in ('PNG','JPEG') or getattr(im,'is_animated',False):
            raise ValueError('only still PNG/JPEG supported')
        width,height=im.size
        if not all(280<=n<=1568 for n in (width,height)):
            raise ValueError('image dimensions must each be 280..1568; no silent resizing')
        fmt='png' if im.format=='PNG' else 'jpg'
        im.verify()
    ref=str(uuid.uuid4())
    payload={'model':model,'state':{'screenshot':ref,'target_instruction':instruction},
        'assets':{ref:{'type':'image','format':fmt,'data_base64':base64.b64encode(data).decode('ascii')}},
        'questions':{
          'presence':{'type':'noul','instructions':'Is at least one GUI element matching `target_instruction` visibly present in `screenshot`? Judge only visible pixels, not elements that may exist offscreen or behind an overlay.'},
          'uniqueness':{'type':'choice','instructions':'How many visibly available GUI elements plausibly match `target_instruction` in `screenshot`? Count all plausible matches; do not arbitrarily choose among them.','criteria':{'none':'No visibly available matching element.','one':'Exactly one visibly available plausible match.','several':'Two or more visibly available plausible matches.'}},
          'localization':{'type':'box','instructions':'The GUI element matching `target_instruction` in `screenshot`.'}}}
    if len(json.dumps(payload).encode())>32*1024*1024:raise ValueError('encoded request exceeds 32 MiB')
    return payload,width,height,hashlib.sha256(data).hexdigest()

class JevClient:
    def __init__(self, log_path, *, max_retries=0, timeout=60, session=None):
        raw_key=os.environ.get('TYPESAFE_API_KEY')
        if not raw_key: raise RuntimeError('TYPESAFE_API_KEY is not set; Jev execution not run')
        self._key=raw_key.strip()
        try:
            self._key.encode('ascii')
        except UnicodeEncodeError as exc:
            raise RuntimeError('TYPESAFE_API_KEY contains hidden non-ASCII characters; re-copy or sanitize it locally') from exc
        if not self._key or any(ch.isspace() for ch in self._key):
            raise RuntimeError('TYPESAFE_API_KEY contains whitespace; re-copy or sanitize it locally')
        if not isinstance(max_retries,int) or not 0<=max_retries<=3:raise ValueError('max_retries must be 0..3')
        self.log_path=Path(log_path);self.log_path.parent.mkdir(parents=True,exist_ok=True)
        self.max_retries=max_retries;self.timeout=timeout;self.session=session or requests.Session()
    def _log(self, record):
        # Defense against accidental credential echoes in error bodies.
        encoded=json.dumps(record,allow_nan=False).replace(self._key,'[REDACTED]')
        with self.log_path.open('a') as f:f.write(encoded+'\n')
    def predict(self, case_id, image_path, instruction):
        payload,width,height,digest=build_payload(image_path,instruction)
        base={'case_id':case_id,'model_name':'Jev','requested_model':MODEL,'model_version':None,
            'prompt_version':PROMPT_VERSION,'question_type':['noul','choice','box'],'provenance':'real_api',
            'image_sha256':digest,'presence_confidence':None,'uniqueness_confidence':None,
            'box_confidence':None,'predicted_box':None,'cost_usd':None}
        total_ms=0
        for attempt in range(self.max_retries+1):
            record={**base,'timestamp':datetime.now(timezone.utc).isoformat(),'attempt':attempt+1,'status':'error','calls':attempt+1}
            start=time.monotonic(); retry=False
            try:
                response=self.session.post(ENDPOINT,headers={'Authorization':'Bearer '+self._key,'TypeSafe-Danger-Zone-Images':'true'},json=payload,timeout=self.timeout)
                record['http_status']=response.status_code
                try:raw=response.json()
                except ValueError:raw={'unparsed_body':response.text}
                record['raw_response']=raw
                if response.status_code != 200:
                    record['error_message']=f'HTTP {response.status_code}; see raw_response'
                    retry=response.status_code in (429,529,500,502,503,504)
                else:
                    record.update(parse_response(raw,width,height))
            except requests.RequestException as exc:
                record['error_message']=type(exc).__name__
                # Network timeouts may have incurred cost. Do not silently resend.
            except ResponseSchemaError as exc:
                record['error_message']=str(exc)
            except (UnicodeError, ValueError, TypeError) as exc:
                # Header/payload construction failures occur before a valid API response.
                # Record only the exception type so a malformed credential is never echoed.
                record['error_message']=f'local request error: {type(exc).__name__}'
            elapsed=(time.monotonic()-start)*1000;total_ms+=elapsed
            record['latency_ms']=elapsed;record['total_latency_ms']=total_ms
            self._log(record)
            if record['status']=='ok' or not retry or attempt==self.max_retries:return record
            delay=2**attempt
            value=response.headers.get('Retry-After')
            if value:
                try:delay=max(delay,float(value))
                except ValueError:return record  # no guessed retry timing
            if delay>60:return record
            time.sleep(delay)
