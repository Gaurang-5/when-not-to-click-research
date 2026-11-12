"""Strict parser for the official TypeSafe schema retrieved 2026-10-17.
No repair, clipping, or confidence imputation: malformed calls are failures.
"""
import math

class ResponseSchemaError(ValueError):
    pass

def _prob(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ResponseSchemaError(f'{name} must be a finite number in [0,1]')
    return float(value)

def parse_response(raw, width, height, expected_model='jev-1.14.0'):
    if not isinstance(raw, dict) or raw.get('model') != expected_model:
        raise ResponseSchemaError('missing or unexpected resolved model version')
    if not all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in (width, height)):
        raise ResponseSchemaError('invalid image dimensions')
    try:
        answers = raw['answers']
        p, u, b = answers['presence'], answers['uniqueness'], answers['localization']
        if (p['type'], u['type'], b['type']) != ('noul','choice','box'):
            raise ResponseSchemaError('unexpected question types')
        presence = _prob(p['noul'], 'noul')
        probabilities = u['probabilities']
        if set(probabilities) != {'none','one','several'}:
            raise ResponseSchemaError('unexpected Choice options')
        probabilities = {k:_prob(v,k) for k,v in probabilities.items()}
        if abs(sum(probabilities.values()) - 1) > 1e-5:
            raise ResponseSchemaError('Choice probabilities do not sum to one')
        if u['choice'] not in probabilities:
            raise ResponseSchemaError('invalid selected option')
        choice_confidence = _prob(u['confidence'],'choice confidence')
        edges = {k:_prob(b['box'][k],k) for k in ('left','top','right','bottom')}
        if edges['left'] >= edges['right'] or edges['top'] >= edges['bottom']:
            raise ResponseSchemaError('degenerate/reversed box')
        box_confidence = _prob(b['confidence'],'box confidence')
        usage = raw['usage']
        if any(isinstance(usage[k],bool) or not isinstance(usage[k],int) or usage[k] < 0 for k in ('input_tokens','output_tokens')):
            raise ResponseSchemaError('invalid usage')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ResponseSchemaError('missing or malformed answer field') from exc
    return dict(model_name='Jev', model_version=raw['model'], status='ok',
        presence_probability=presence, presence_confidence=presence,
        uniqueness_probability=probabilities['one'], uniqueness_confidence=probabilities['one'],
        match_choice=u['choice'], match_probabilities=probabilities, choice_confidence=choice_confidence,
        box_confidence=box_confidence, normalized_box=edges,
        predicted_box=[edges['left']*width,edges['top']*height,edges['right']*width,edges['bottom']*height],
        usage=usage, cost_usd=usage['input_tokens']*0.042/1_000_000)
