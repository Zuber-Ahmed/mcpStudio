"""Foundation canonicalization boundary, using the unchanged contract and pinned dev tools.

This validates contract structure, not plugin installation, source truth or secret safety.
"""
from copy import deepcopy
from pathlib import Path
import hashlib,json,sys,uuid
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work/python-tools'))
import rfc8785
from jsonschema import RefResolver
from openapi_schema_validator import OAS30Validator

def strict_json(text):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    def invalid(value):raise ValueError('nonfinite JSON number')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid)

def unique_sorted(values,key=lambda value:value):
    identities=[key(value) for value in values]
    if len(set(identities))!=len(identities):raise ValueError('duplicate set identity')
    return sorted(values,key=lambda value:key(value).encode('utf-16-be'))

def canonical_plan_bytes(plan):
    p=deepcopy(plan)
    for key in ['snapshot_id','analysis_id','recommendation_id']:p[key]=str(uuid.UUID(p[key]))
    p['source_digest']=p['source_digest'].lower()
    p['policy']['id']=str(uuid.UUID(p['policy']['id']))
    p['policy']['required_checks']=unique_sorted(p['policy']['required_checks'])
    p['analyzer_versions']=unique_sorted(p['analyzer_versions'],lambda value:value['id'])
    for candidate in p['candidates']:
        candidate['id']=str(uuid.UUID(candidate['id']))
        candidate['required_scopes']=unique_sorted(candidate['required_scopes'])
    p['candidates']=unique_sorted(p['candidates'],lambda value:value['id'])
    api=json.loads((ROOT/'packages/contracts/specs/openapi.yaml').read_text(encoding='utf-8'))
    validator=OAS30Validator(api['components']['schemas']['CanonicalPlan'],resolver=RefResolver.from_schema(api),format_checker=OAS30Validator.FORMAT_CHECKER)
    validator.validate(p)
    # rfc8785 rejects nonfinite, malformed Unicode and integers outside the safe range.
    return rfc8785.dumps(p)

def plan_hash(plan):return hashlib.sha256(canonical_plan_bytes(plan)).hexdigest()
