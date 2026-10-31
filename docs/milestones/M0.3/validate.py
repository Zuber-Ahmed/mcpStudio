"""Limited contract-design checker. NOT a full OpenAPI or server validator."""
import copy
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parent
api = json.loads((ROOT/'specs/openapi.yaml').read_text())
schemas = api['components']['schemas']
checks, fixtures = [], []
def check(name, ok):
    checks.append({'name':name,'passed':bool(ok)})
def resolve(ref):
    value=api
    if not ref.startswith('#/'):
        raise ValueError('external reference unsupported')
    for p in ref[2:].split('/'):
        value=value[p.replace('~1','/').replace('~0','~')]
    return value

def valid(value, schema):
    """Only the instance-keyword subset used here; no meta-schema validation."""
    if '$ref' in schema:
        return valid(value,resolve(schema['$ref']))
    if value is None and schema.get('nullable'):
        return True
    if 'allOf' in schema and not all(valid(value,s) for s in schema['allOf']):
        return False
    if 'anyOf' in schema and not any(valid(value,s) for s in schema['anyOf']):
        return False
    if 'oneOf' in schema and sum(valid(value,s) for s in schema['oneOf']) != 1:
        return False
    if 'not' in schema and valid(value,schema['not']):
        return False
    typ=schema.get('type')
    matches={'object':isinstance(value,dict),'array':isinstance(value,list),
        'string':isinstance(value,str),'integer':isinstance(value,int) and not isinstance(value,bool),
        'number':isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value),
        'boolean':isinstance(value,bool)}
    if typ and not matches[typ]:
        return False
    if 'enum' in schema and not any(type(value) is type(x) and value==x for x in schema['enum']):
        return False
    if isinstance(value,dict):
        if any(x not in value for x in schema.get('required',[])):
            return False
        props=schema.get('properties',{})
        if schema.get('additionalProperties') is False and any(x not in props for x in value):
            return False
        if not all(valid(v,props[k]) for k,v in value.items() if k in props):
            return False
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',float('inf')):
            return False
        if schema.get('uniqueItems') and len({json.dumps(v,sort_keys=True) for v in value})!=len(value):
            return False
        if 'items' in schema and not all(valid(v,schema['items']) for v in value):
            return False
    if isinstance(value,str):
        if len(value)<schema.get('minLength',0) or len(value)>schema.get('maxLength',float('inf')):
            return False
        if 'pattern' in schema and not re.search(schema['pattern'],value):
            return False
        try:
            if schema.get('format')=='uuid': UUID(value)
            if schema.get('format')=='date-time': datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError:
            return False
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        if value<schema.get('minimum',-float('inf')) or value>schema.get('maximum',float('inf')):
            return False
    return True

ops=[(p,m,o) for p,methods in api['paths'].items() for m,o in methods.items()]
ids=[o['operationId'] for _,_,o in ops]
check('24 unique operation IDs',len(ids)==len(set(ids))==24)
check('43 resource schemas',len(schemas)==43)
old=json.loads((ROOT.parent/'M0.1/sources/technical-documentation/specs/openapi.yaml').read_text())
oldids={o['operationId'] for methods in old['paths'].values() for o in methods.values()}
check('all original 15 operation IDs retained',oldids.issubset(ids))
def walk(obj):
    if isinstance(obj,dict):
        if '$ref' in obj:
            try: resolve(obj['$ref']); check('reference:'+obj['$ref'],True)
            except (KeyError,ValueError): check('reference:'+obj['$ref'],False)
        if 'required' in obj and 'properties' in obj and obj.get('additionalProperties') is False:
            check('required fields declared',set(obj['required']).issubset(obj['properties']))
        for v in obj.values(): walk(v)
    elif isinstance(obj,list):
        for v in obj: walk(v)
walk(api)
semantics=(ROOT/'semantic-rules.md').read_text()
for path,method,op in ops:
    params=op.get('parameters',[])
    check('path:'+op['operationId'],set(re.findall(r'\{([^}]+)\}',path))==
          {p['name'] for p in params if p.get('in')=='path' and p.get('required') is True})
    check('no per-op auth bypass:'+op['operationId'],'security' not in op or bool(op['security']))
    if method=='post':
        check('idempotency:'+op['operationId'],any(p['name']=='Idempotency-Key' and p['required'] for p in params))
    for rule in op.get('x-semantic-rules',[]):
        check('semantic definition:'+rule,rule in semantics)
dictionary=json.loads((ROOT/'specs/data-dictionary.json').read_text())
check('23 entities',len(dictionary['entities'])==23)
check('32 relationships',len(dictionary['relationships'])==32)
check('relationship endpoints exist',all(r['parent'] in dictionary['entities'] and r['child'] in dictionary['entities'] for r in dictionary['relationships']))
erd=(ROOT/'specs/database-erd.mmd').read_text()
for entity,fields in dictionary['entities'].items():
    check('ERD entity:'+entity, bool(re.search(r'^  '+entity+r' \{',erd,re.M)))
    for name in fields:
        body=re.search(r'^  '+entity+r' \{\n(.*?)^  \}',erd,re.M|re.S).group(1)
        check('ERD field:'+entity+'.'+name, bool(re.search(r'\b'+name+r'$',body,re.M)))

def case(name,schema,value,expected):
    actual=valid(value,schemas[schema])
    fixtures.append(dict(name=name,schema=schema,value=value,expected=expected,actual=actual))
    check('fixture:'+name,actual==expected)
uid='00000000-0000-4000-8000-000000000001'
sha='a'*64
scope={'version':'1','endpoints':True,'protocol_schemas':True,'prompts_resources':False,'dependency_graph':True}
case('local revision optional','Source',{'kind':'local','location':'fixture'},True)
case('git revision required','Source',{'kind':'git','location':'https://example.test/repo'},False)
case('git revision accepted','Source',{'kind':'git','location':'https://example.test/repo','revision':'abc123'},True)
case('raw token rejected','Source',{'kind':'local','location':'fixture','token':'fixture-secret'},False)
analysis={'project_id':uid,'scope':scope,'semantic_mode':'disabled'}
case('offline analysis','AnalysisInput',analysis,True)
case('consent missing','AnalysisInput',dict(analysis,semantic_mode='consented'),False)
case('explicit consent reference','AnalysisInput',dict(analysis,semantic_mode='consented',consent_reference=uid),True)
case('disabled mode rejects consent baggage','AnalysisInput',dict(analysis,consent_reference=uid),False)
case('untrusted command rejected','AnalysisInput',dict(analysis,command='execute-source'),False)
executed={'name':'compile','mandatory':True,'status':'passed','finding_ids':[], 'command':'tsc --noEmit',
          'tool_version':'pinned-fixture','exit_code':0,'started_at':'2026-10-28T10:00:00Z',
          'completed_at':'2026-10-28T10:00:01Z','log_reference':'redacted-log-1'}
case('executed evidence accepted','Check',executed,True)
missing=copy.deepcopy(executed);del missing['exit_code']
case('passed without exit evidence denied','Check',missing,False)
case('skip reason required','Check',{'name':'compile','mandatory':True,'status':'skipped','finding_ids':[]},False)
skip={'name':'compile','mandatory':True,'status':'skipped','finding_ids':[],'reason':'tool unavailable'}
case('truthful skip accepted','Check',skip,True)
case('skip cannot forge execution','Check',dict(skip,exit_code=0),False)
case('security confirmation false denied','ApprovalInput',{'plan_version':1,'plan_hash':sha,'security_confirmed':False},False)
case('empty required-check policy denied','PolicyReference',{'id':'mvp','version':'1','required_checks':[]},False)
case('duplicate required checks denied','PolicyReference',{'id':'mvp','version':'1','required_checks':['compile','compile']},False)
case('graph cannot silently truncate','Graph',{'analysis_id':uid,'nodes':[],'edges':[],'truncated':True},False)

resource_api, resource_schemas = api, schemas
api = json.loads((ROOT/'specs/bootstrap.openapi.yaml').read_text())
schemas = api['components']['schemas']
walk(api)
bootstrap_ops=[o for methods in api['paths'].values() for o in methods.values()]
check('3 distinct bootstrap operations',len({o['operationId'] for o in bootstrap_ops})==3)
check('bootstrap does not redefine resource operations',not {o['operationId'] for o in bootstrap_ops}.intersection(ids))
case('bootstrap exact nonce/code shape','BootstrapExchange',{'one_time_code':'a'*43,'browser_nonce':'b'*43},True)
case('bootstrap short secret denied','BootstrapExchange',{'one_time_code':'short','browser_nonce':'b'*43},False)
case('bootstrap nonce required','BootstrapExchange',{'one_time_code':'a'*43},False)
case('bootstrap arbitrary tenant denied','BootstrapExchange',{'one_time_code':'a'*43,'browser_nonce':'b'*43,'tenant_id':uid},False)
api, schemas = resource_api, resource_schemas

# Semantic reference oracle against contract scenarios, not production authorization code.
def export_gate(c):
    required=c['required_checks']; checks_by_name={x['name']:x for x in c['checks']}
    if not c['authorized'] or c['revoked'] or c['generation_status']!='succeeded' or not c['runner_finished']:
        return False
    if not required or len(required)!=len(set(required)) or len(checks_by_name)!=len(c['checks']):
        return False
    if c['generation_digest']!=c['validation_digest'] or c['plan_policy']!=c['validation_policy']:
        return False
    for name in required:
        row=checks_by_name.get(name)
        if not row or row['status']!='passed' or row.get('exit_code')!=0 or not valid(row,schemas['Check']):
            return False
        if datetime.fromisoformat(row['completed_at'].replace('Z','+00:00')) < datetime.fromisoformat(row['started_at'].replace('Z','+00:00')):
            return False
    return True
context=dict(authorized=True,revoked=False,generation_status='succeeded',runner_finished=True,
    required_checks=['compile'],checks=[executed],generation_digest=sha,validation_digest=sha,
    plan_policy='mvp:1',validation_policy='mvp:1')
def gatecase(name,value,expected):
    actual=export_gate(value)
    fixtures.append(dict(name=name,semantic_rule='SEM-EXPORT',value=value,expected=expected,actual=actual))
    check('semantic fixture:'+name,actual==expected)
gatecase('matching complete evidence',context,True)
for name,changes in [
    ('empty mandatory list',{'required_checks':[]}),('mandatory skipped',{'checks':[skip]}),
    ('mandatory absent',{'checks':[]}),('missing actor rights',{'authorized':False}),
    ('revoked approval',{'revoked':True}),('unfinished runner',{'runner_finished':False}),
    ('changed artifact bytes',{'validation_digest':'b'*64}),('changed policy',{'validation_policy':'mvp:2'}),
    ('generation failed',{'generation_status':'failed'}),('missing evidence',{'checks':[missing]}),
    ('forged passed exit',{'checks':[dict(executed,exit_code=1)]}),
    ('reverse execution time',{'checks':[dict(executed,completed_at='2026-10-28T09:00:00Z')]}),
    ('duplicate check records',{'checks':[executed,executed]})]:
    gatecase(name,dict(context,**changes),False)

# Constrained canonical vectors only: no Unicode/float/full RFC8785 claim.
vectors=[]
for value in [{},{'b':2,'a':1},[{'path':'a.txt','sha256':'0'*64,'size_bytes':0}]]:
    canonical=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)
    vectors.append({'input':value,'canonical':canonical,'sha256':hashlib.sha256(canonical.encode()).hexdigest()})
(ROOT/'canonical-vectors.json').write_text(json.dumps(vectors,indent=2)+'\n')
node_script=ROOT/'verify-vectors.cjs'
node_result=subprocess.run(['node',str(node_script)],capture_output=True,text=True)
check('Python/Node ASCII integer vector agreement',node_result.returncode==0)
(ROOT/'contract-fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n')
files=['specs/openapi.yaml','specs/bootstrap.openapi.yaml','specs/database-erd.mmd','specs/data-dictionary.json','semantic-rules.md','version-pins.json']
report={'scope':'Limited structural and contract-design fixtures only','passed':all(c['passed'] for c in checks),
    'check_count':len(checks),'fixture_count':len(fixtures),'failed':[c for c in checks if not c['passed']],
    'operations':len(ops),'bootstrap_operations':len(bootstrap_ops),'schemas':len(schemas),'entities':len(dictionary['entities']),
    'sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files},
    'full_openapi_validator':'not run; dependency download DNS failure',
    'client_generation':'not run; dependency retrieval unavailable',
    'full_rfc8785_test':'not run; subset vectors only',
    'database_constraint_tests':'not run; no database/engine', 'mcp_interoperability':'not run',
    'runtime_tests_executed':0,'ready_for_initialization':False}
(ROOT/'validation-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
