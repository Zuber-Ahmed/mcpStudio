"""Synchronize approved M0.2 amendment into reviewable contracts, never source evidence."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / 'specs'
SPEC.mkdir(exist_ok=True)
old = ROOT.parent / 'M0.1/sources/technical-documentation/specs/openapi.yaml'
api = json.loads(old.read_text(encoding='utf-8'))
api['info'].update(title='MCP Integration Studio Control API', version='0.2.0-review',
    description='Synchronized approved M0.2 design. Local operator Studio; implementation and readiness unverified. See semantic-rules.md for cross-resource gates.')
S = api['components']['schemas']
ref = lambda n: {'$ref': '#/components/schemas/' + n}
string = lambda **kw: dict(type='string', **kw)
uuid = lambda: string(format='uuid')
digest = lambda: string(pattern='^[a-f0-9]{64}$')
time = lambda: string(format='date-time')
enum = lambda *v: string(enum=list(v))
integer = lambda **kw: dict(type='integer', **kw)
array = lambda x, **kw: dict(type='array', items=x, **kw)
obj = lambda p, req=None, **kw: dict(type='object', additionalProperties=False,
    properties=p, required=list(p) if req is None else req, **kw)
nullable_uuid = lambda: dict(type='string', format='uuid', nullable=True)
PROVENANCE = enum('deterministic', 'model', 'manual', 'unknown')
STATUS = enum('created','analyzing','generating','validating','blocked','validated','generated','needs_confirmation','ready_for_review')
MODES = enum('server','client','both','none')
S['Error']['properties']['reasons'] = array(string())
S['Source'] = obj({'kind': enum('local','git'), 'location': string(minLength=1),
    'revision': string(minLength=1), 'credential_reference': string(minLength=1)}, ['kind','location'])
S['Source']['oneOf'] = [
    {'properties': {'kind': enum('local')}},
    {'properties': {'kind': enum('git')}, 'required': ['revision']}]
S['Source']['description'] = 'Git requires revision; local revision optional. Acquisition resolves immutable snapshot; raw credentials prohibited.'
S['Project']['properties'].update(updated_at=time(), workflow_status=STATUS,
    latest_analysis_id=nullable_uuid(), latest_plan_id=nullable_uuid(),
    latest_generation_id=nullable_uuid(), latest_validation_id=nullable_uuid())
S['Project']['required'] += ['updated_at','workflow_status','latest_analysis_id','latest_plan_id','latest_generation_id','latest_validation_id']
S['AnalysisScope'] = obj({'version': enum('1'), 'endpoints': {'type':'boolean'},
    'protocol_schemas': {'type':'boolean'}, 'prompts_resources': {'type':'boolean'}, 'dependency_graph': {'type':'boolean'}})
S['AnalysisInput']['properties'].update(scope=ref('AnalysisScope'), semantic_mode=enum('disabled','consented'),
    consent_reference=uuid(), previous_run_id=uuid())
S['AnalysisInput']['required'] += ['scope','semantic_mode']
S['AnalysisInput']['oneOf'] = [
    {'properties': {'semantic_mode': enum('disabled')}, 'not': {'required':['consent_reference']}},
    {'properties': {'semantic_mode': enum('consented')}, 'required':['consent_reference']}]
S['Analysis']['properties'].update(snapshot_id=uuid(), resolved_revision=string(),
    analyzer_versions=array(ref('VersionReference')), scope=ref('AnalysisScope'))
S['VersionReference'] = obj({'id':string(minLength=1),'version':string(minLength=1)})
S['Confidence'] = obj({'value': {'type':'number','minimum':0,'maximum':1,'nullable':True},
    'method': string(minLength=1)})
S['Node']['properties'].update(provenance=PROVENANCE, confidence=ref('Confidence'))
S['Node']['required'] += ['provenance','confidence']
S['Edge']['properties'].update(provenance=PROVENANCE, evidence=array(ref('Evidence')))
S['Edge']['required'] += ['provenance']
S['Graph']['properties']['truncated'] = {'type':'boolean','enum':[False]}
S['Graph']['required'].append('truncated')
S['Candidate'] = obj({'id':uuid(),'finding_id':string(minLength=1),'graph_node_id':uuid(),
    'operation_type':enum('read','write','unknown'),'side_effects':array(string()),
    'sensitivity':enum('public','internal','sensitive','unknown'),'required_scopes':array(string()),
    'input_schema':{'type':'object','additionalProperties':True},
    'output_schema':{'type':'object','additionalProperties':True},
    'eligibility':enum('allowed','blocked','unsupported','unknown'), 'reason_codes':array(string()),
    'evidence':array(ref('Evidence')), 'detector':ref('VersionReference'),
    'provenance':PROVENANCE,'confidence':ref('Confidence')})
S['Candidate']['allOf'] = [{'oneOf':[
    {'properties':{'eligibility':enum('allowed'),'operation_type':enum('read'),
                   'evidence':array(ref('Evidence'),minItems=1)}},
    {'properties':{'eligibility':enum('blocked','unsupported','unknown')}}]}]
S['Recommendation'] = obj({'id':uuid(),'version':integer(minimum=1),'analysis_id':uuid(),
    'source_digest':digest(),'recommended_type':MODES,'rationale':string(minLength=1),
    'candidate_ids':array(uuid(),uniqueItems=True),'risks':array(string()),'required_reviews':array(string()),
    'supported_generation':{'type':'boolean'},'availability_reason':string()})
S['Configuration'] = obj({'plugin':ref('VersionReference'),'schema':ref('VersionReference'),
    'values':{'type':'object','additionalProperties':True}})
S['Configuration']['description'] = 'Non-secret values require plugin schema validation. Only opaque secret references; never credentials.'
S['PolicyReference'] = obj({'id':string(minLength=1),'version':string(minLength=1),
    'required_checks':array(string(minLength=1),minItems=1,uniqueItems=True)})
S['PlanInput']['properties'].update(recommendation_id=uuid(),recommendation_version=integer(minimum=1),
    override_reason=string(minLength=1))
S['PlanInput']['required'] += ['recommendation_id','recommendation_version']
S['PlanInput']['properties']['capability_ids']['uniqueItems'] = True
S['Plan'] = copy.deepcopy(S['PlanInput'])
S['CanonicalPlan'] = obj({'snapshot_id':uuid(),'source_digest':digest(),'analysis_id':uuid(),
    'analyzer_versions':array(ref('VersionReference'),minItems=1), 'recommendation_id':uuid(),
    'recommendation_version':integer(minimum=1),'selected_type':MODES,
    'candidates':array(ref('ExecutableCandidate'),uniqueItems=True), 'generator':ref('VersionReference'),
    'configuration':ref('Configuration'),'transport':enum('stdio'),'policy':ref('PolicyReference'),
    'override_reason':string(nullable=True)})
S['ExecutableCandidate'] = obj({'id':uuid(),'input_schema':{'type':'object','additionalProperties':True},
    'output_schema':{'type':'object','additionalProperties':True},'domain_service_reference':string(minLength=1),
    'required_scopes':array(string(),uniqueItems=True)})
S['Plan']['properties'].update(id=uuid(),version=integer(minimum=1),status=enum('draft','approved','superseded','revoked'),
    content_hash=digest(),canonicalization=enum('RFC8785+MCPStudio-sets-v1'),
    canonical_payload=ref('CanonicalPlan'),policy_version=string(),rationale=string(),risks=array(string()))
S['Plan']['required'] += ['id','version','status','content_hash','canonicalization','canonical_payload','policy_version','rationale','risks']
S['Approval']['properties'].update(plan_version=integer(minimum=1),security_confirmed={'type':'boolean','enum':[True]},
    revoked_at=string(format='date-time',nullable=True))
S['Approval']['required'] += ['plan_version','security_confirmed','revoked_at']
S['GenerationInput']['properties']['previous_run_id'] = uuid()
S['Generation']['properties'].update(plan_hash=digest(),generator=ref('VersionReference'),artifact_set_digest=digest())
S['Generation']['required'] += ['plan_hash','generator']
S['ValidationInput']['properties']['previous_run_id'] = uuid()
S['Check']['properties'].update(reason=string(minLength=1),finding_ids=array(string(),uniqueItems=True))
S['Check']['required'].append('finding_ids')
S['Check']['oneOf'] = [
    {'properties':{'status':enum('passed','failed')},'required':['command','tool_version','exit_code','started_at','completed_at','log_reference']},
    {'properties':{'status':enum('skipped','not_run')},'required':['reason'],
     'not':{'anyOf':[{'required':[n]} for n in ['exit_code','started_at','completed_at']]}}]
S['Check']['description'] = 'Passed requires exit_code=0; failed requires evidence and truthful status; skipped/not_run must not forge execution. Semantic gates apply.'
S['Validation']['properties'].update(artifact_set_digest=digest(),policy=ref('PolicyReference'))
S['Validation']['required'] += ['artifact_set_digest','policy']
S['Validation']['properties']['checks']['minItems'] = 1
S['Validation']['description'] = 'Queued/running uses not_run records for pinned required checks. Succeeded still requires semantic policy/manifest/runner checks.'
S['Artifact']['properties'].update(status=enum('draft','blocked','validated','approved'),
    finding_ids=array(string(),uniqueItems=True),check_names=array(string(),uniqueItems=True))
S['Artifact']['required'] += ['status','finding_ids','check_names']
S['ArtifactPreview'] = obj({'artifact_id':uuid(),'sha256':digest(),'media_type':string(),
    'encoding':enum('utf-8'),'offset':integer(minimum=0),'content':string(),
    'truncated':{'type':'boolean'},'next_offset':integer(minimum=0,nullable=True)})
S['RunSummary'] = obj({'id':uuid(),'kind':enum('analysis','generation','validation'),
    'status':enum('queued','running','succeeded','partial','failed','cancelled'),
    'created_at':time(),'completed_at':string(format='date-time',nullable=True),
    'previous_run_id':nullable_uuid()})
S['PluginCapability'] = obj({'plugin':ref('VersionReference'),'applications':array(string()),
    'generation_modes':array(MODES),'transports':array(enum('stdio')),
    'configuration_schema':ref('VersionReference'),'available':{'type':'boolean'},'reason':string()})
S['Capabilities'] = obj({'plugins':array(ref('PluginCapability')),'semantic_available':{'type':'boolean'}})
S['LogPage'] = obj({'validation_id':uuid(),'entries':array(ref('LogEntry')),'next_cursor':string(nullable=True)})
S['LogEntry'] = obj({'check_name':string(),'timestamp':time(),'level':enum('info','warning','error'),
    'text':string(),'finding_ids':array(string())})
S['Finding'] = obj({'id':string(),'severity':enum('info','warning','blocking'),'code':string(),
    'message':string(),'evidence':array(ref('Evidence'))})
S['GenerationReport'] = obj({'generation_id':uuid(),'plan_hash':digest(),'artifact_set_digest':digest(),
    'policy':ref('PolicyReference'),'approval_status':enum('draft','approved','revoked'),
    'findings':array(ref('Finding')),'checks':array(ref('Check'))})
S['RevocationInput'] = obj({'plan_version':integer(minimum=1),'plan_hash':digest(),'reason':string(minLength=1)})
S['Revocation'] = obj({'id':uuid(),'plan_id':uuid(),'actor_id':uuid(),'revoked_at':time(),'reason':string()})
for name, item in [('CandidateList','Candidate'),('RunList','RunSummary')]:
    S[name] = obj({'items':array(ref(item)),'next_cursor':string(nullable=True)},['items'])
def query(name, schema, required=False, desc=''):
    return dict(name=name, **{'in':'query'}, required=required, schema=schema, description=desc)
def pagination(maximum=100, default=25):
    return [query('cursor',string()),query('limit',integer(minimum=1,maximum=maximum,default=default))]
errors = copy.deepcopy(api['paths']['/projects']['get']['responses'])
errors.pop('200',None)
def operation(path, method, opid, output, request=None, code='200', desc=''):
    o = {'operationId':opid,'summary':opid,'description':desc,'responses':copy.deepcopy(errors)}
    o['responses'][code] = {'description':'Success','content':{'application/json':{'schema':ref(output)}}}
    o['parameters'] = [{'name':n,'in':'path','required':True,'schema':uuid()} for n in __import__('re').findall(r'\{([^}]+)\}',path)]
    if request:
        o['requestBody']={'required':True,'content':{'application/json':{'schema':ref(request)}}}
    api['paths'].setdefault(path,{})[method]=o
    return o
api['paths']['/projects']['get']['parameters'] = pagination() + [query('q',string(maxLength=200)),query('status',STATUS)]
operation('/projects/{project_id}/runs','get','listProjectRuns','RunList')['parameters'] += pagination()
operation('/capabilities','get','getSupportedCapabilities','Capabilities')
operation('/analyses/{analysis_id}/candidates','get','listCandidates','CandidateList')['parameters'] += pagination()
operation('/analyses/{analysis_id}/recommendation','get','getRecommendation','Recommendation')
preview = operation('/artifacts/{artifact_id}/content','get','getArtifactContent','ArtifactPreview',desc='Authorized bounded UTF-8 preview; unsupported binary preview returns 422. No storage path disclosure.')
preview['parameters'] += [query('offset',integer(minimum=0,default=0)),query('limit',integer(minimum=1,maximum=262144,default=262144))]
operation('/validations/{validation_id}/logs','get','getValidationLogs','LogPage')['parameters'] += pagination()
report = operation('/generations/{generation_id}/report','get','getGenerationReport','GenerationReport')
report['parameters'] += [query('format',enum('json','markdown','pdf'),True)]
report['responses']['200']['content'].update({'text/markdown':{'schema':string()},'application/pdf':{'schema':string(format='binary')}})
draft = operation('/generations/{generation_id}/draft-bundle','get','downloadDraftBundle','GenerationReport',desc='Local operator only, finalized output, secret-safe draft; audited and never changes approval state.')
draft['parameters'] += [{'name':'X-Draft-Acknowledgement','in':'header','required':True,
    'schema':enum('DRAFT-NOT-APPROVED')}]
draft['responses']['200']['content']={'application/zip':{'schema':string(format='binary')}}
operation('/plans/{plan_id}/revocations','post','revokePlanApproval','Revocation','RevocationInput','201')
for path, methods in api['paths'].items():
    for method, op in methods.items():
        if method == 'post':
            op.setdefault('parameters',[]).append({'name':'Idempotency-Key','in':'header','required':True,
                'schema':string(minLength=16,maxLength=128,pattern='^[A-Za-z0-9_-]+$'),
                'description':'Scoped to tenant/operator/operation; same key/body replays, changed body returns 409.'})
            op['x-semantic-rules']=['SEM-AUTH','SEM-IDEMPOTENCY']
        else:
            op['x-semantic-rules']=['SEM-AUTH']
api['paths']['/plans']['post']['x-semantic-rules'] += ['SEM-PLAN','SEM-CANDIDATE']
api['paths']['/plans/{plan_id}/approvals']['post']['x-semantic-rules'] += ['SEM-APPROVAL']
api['paths']['/generations']['post']['x-semantic-rules'] += ['SEM-APPROVAL','SEM-GENERATION']
api['paths']['/generations/{generation_id}/bundle']['get']['x-semantic-rules'] += ['SEM-EXPORT']
api['paths']['/generations/{generation_id}/draft-bundle']['get']['x-semantic-rules'] += ['SEM-DRAFT']
api['paths']['/analyses']['post']['x-semantic-rules'] += ['SEM-CONSENT']
api['paths']['/validations']['post']['x-semantic-rules'] += ['SEM-VALIDATION']
api['paths']['/artifacts']['get']['parameters'] = [query('generation_id',uuid(),True)] + pagination()
api['x-contract-amendment'] = 'M0.2 CA01-CA08; semantic-rules.md; 0.2.0-review'
api['components']['securitySchemes']['localSession'] = {'type':'apiKey','in':'cookie',
    'name':'mcpstudio_session','description':'HttpOnly local session; exact Origin and CSRF required for cookie-auth mutations. Host bootstrap contract is a readiness hold.'}
api['security'] = [{'bearerAuth':[]},{'localSession':[]}]
for methods in api['paths'].values():
    for method, op in methods.items():
        if method == 'post':
            op['parameters'].append({'name':'X-CSRF-Token','in':'header','required':False,
                'schema':string(minLength=32),'description':'Mandatory when using localSession cookie; ignored as authority for bearer auth. Exact Origin validation is also mandatory.'})
api['x-initial-support'] = {'generation':['server'],'transport':['stdio'],'semantic_inference':'disabled-until-provisioned'}
(SPEC/'openapi.yaml').write_text(json.dumps(api,indent=2)+'\n',encoding='utf-8')
inventory = [{'operationId':o['operationId'],'method':m.upper(),'path':p,
    'semantic_rules':o.get('x-semantic-rules',[])} for p, methods in api['paths'].items() for m,o in methods.items()]
(ROOT/'operation-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
print(f'Wrote {len(inventory)} operations and {len(S)} schemas')

# Logical ERD and dictionary share a single declarative source. No migrations executed.
import re
original_erd = (old.parent/'database-erd.mmd').read_text(encoding='utf-8')
entities = {}
for name, body in re.findall(r'^  ([A-Z_]+) \{\n(.*?)^  \}', original_erd, re.M|re.S):
    entities[name] = {line.split()[1]:line.split()[0] for line in body.splitlines() if line.strip()}
def fields(entity, **kwargs):
    entities.setdefault(entity, {}).update(kwargs)
fields('PROJECT', updated_at='datetime')
fields('ANALYSIS_RUN', snapshot_id='uuid', resolved_revision='string', analyzer_versions='json',
       scope='json', semantic_mode='string', consent_id='uuid', previous_run_id='uuid', completed_at='datetime')
fields('GRAPH_NODE', label='string', provenance='string', confidence='json')
fields('GRAPH_EDGE', provenance='string', evidence='json')
fields('PLAN', snapshot_id='uuid', recommendation_id='uuid', recommendation_version='int',
       candidate_ids='json', rationale='string', risks='json', canonical_payload='json',
       canonicalization='string', generator='json', policy_id='uuid', override_reason='string', is_current='boolean')
fields('APPROVAL', plan_version='int', security_confirmed='boolean', revoked_at='datetime')
fields('GENERATION_RUN', plan_hash='string', generator='json', artifact_set_digest='string',
       previous_run_id='uuid', completed_at='datetime')
fields('VALIDATION_RUN', artifact_set_digest='string', policy_id='uuid',
       previous_run_id='uuid', completed_at='datetime')
fields('VALIDATION_CHECK', command='string', tool_version='string', started_at='datetime',
       completed_at='datetime', reason='string', finding_ids='json')
base = dict(id='uuid', tenant_id='uuid')
def extra(name, **kw):
    entities[name] = dict(base, **kw)
extra('SOURCE_SNAPSHOT', project_id='uuid', source_digest='string', storage_key='string',
      resolved_revision='string', created_at='datetime')
extra('CANDIDATE', analysis_run_id='uuid', graph_node_id='uuid', finding_id='string',
      operation_type='string', side_effects='json', sensitivity='string', required_scopes='json',
      input_schema='json', output_schema='json', eligibility='string', reason_codes='json',
      evidence='json', detector='json', provenance='string', confidence='json')
extra('RECOMMENDATION', analysis_run_id='uuid', version='int', source_digest='string',
      recommended_type='string', rationale='string', candidate_ids='json', risks='json',
      required_reviews='json', supported_generation='boolean', availability_reason='string')
extra('POLICY', policy_key='string', version='string', required_checks='json', schema_version='string',
      content_hash='string')
extra('INFERENCE_CONSENT', project_id='uuid', actor_id='uuid', source_digest='string', provider_id='string',
      payload_classes='json', redaction_policy='string', retention_disclosure='string', expires_at='datetime',
      revoked_at='datetime')
extra('IDEMPOTENCY_RECORD', actor_id='uuid', operation_id='string', key='string', request_digest='string',
      resource_id='uuid', status='string', response='json', created_at='datetime')
extra('OUTBOX_EVENT', aggregate_id='uuid', event_type='string', payload='json',
      created_at='datetime', dispatched_at='datetime', delivery_attempts='int')
extra('FINDING', generation_run_id='uuid', stable_key='string', severity='string', code='string',
      message='string', evidence='json')
extra('PLAN_REVOCATION', plan_id='uuid', actor_id='uuid', reason='string', revoked_at='datetime')
relations = re.findall(r'^  ([A-Z_]+) \|\|--o\{ ([A-Z_]+) : (.+)$',original_erd,re.M)
relations += [('PROJECT','SOURCE_SNAPSHOT','snapshots'),('SOURCE_SNAPSHOT','ANALYSIS_RUN','analyzed_as'),
    ('ANALYSIS_RUN','CANDIDATE','discovers'),('GRAPH_NODE','CANDIDATE','grounds'),
    ('ANALYSIS_RUN','RECOMMENDATION','recommends'),('RECOMMENDATION','PLAN','informs'),
    ('POLICY','PLAN','pins'),('POLICY','VALIDATION_RUN','governs'),
    ('PROJECT','INFERENCE_CONSENT','permits'),('GENERATION_RUN','FINDING','reports'),
    ('PLAN','PLAN_REVOCATION','revoked_by'),('USER','PLAN_REVOCATION','records'),
    ('TENANT','IDEMPOTENCY_RECORD','deduplicates'),('TENANT','OUTBOX_EVENT','schedules')]
erd = ['%% M0.3 synchronized logical contract; no physical DDL enforced.', 'erDiagram']
erd += [f'  {a} ||--o{{ {b} : {label}' for a,b,label in relations]
for name, props in entities.items():
    erd.append(f'  {name} {{')
    erd += [f'    {typ} {key}' for key,typ in props.items()]
    erd.append('  }')
(SPEC/'database-erd.mmd').write_text('\n'.join(erd)+'\n',encoding='utf-8')
constraints = [
 {'id':'DB01','rule':'Each tenant-owned table exposes UNIQUE(tenant_id,id); parent references include tenant_id.'},
 {'id':'DB02','rule':'Graph edge from/to and candidate node must belong to same analysis and tenant.'},
 {'id':'DB03','rule':'Plan UNIQUE(tenant_id,analysis_run_id,version); partial unique current plan per analysis; monotonic version under lock.'},
 {'id':'DB04','rule':'Generation composite approval FK includes tenant_id,plan_id,approval_id; require current nonrevoked version/hash and current actor rights transactionally.'},
 {'id':'DB05','rule':'Plan recommendation and snapshot must belong to its analysis; candidate IDs must all belong to same tenant/analysis and match canonical payload.'},
 {'id':'DB06','rule':'Validation artifact_set_digest and policy must equal immutable generation/approved plan; semantic trigger/service admission plus transaction test.'},
 {'id':'DB07','rule':'Policy required_checks nonempty and unique; validation check unique(tenant_id,validation_run_id,name); executed and skipped field rules match OpenAPI.'},
 {'id':'DB08','rule':'Idempotency UNIQUE(tenant_id,actor_id,operation_id,key); digest conflict 409; outbox stable aggregate event identity prevents repeated effects.'},
 {'id':'DB09','rule':'No cascade deletion of audit/approval/validation; terminal runs require completed_at; hashes lowercase SHA256; relative safe artifact paths; no credentials.'},
 {'id':'DB10','rule':'Consent matches tenant/project/actor/source digest/provider/payload policy/expiry and is not revoked; never consent by unchecked JSON.'}]
dictionary={'version':'0.2.0-review','entities':entities,
    'relationships':[{'parent':a,'child':b,'label':l,'cardinality':'one-to-zero-or-many'} for a,b,l in relations],
    'constraints':constraints,'physical_migrations_applied':False,
    'notes':'ERD is logical. Nullable parent references and conditional cross-field checks require physical design; see semantic-rules.md.'}
(SPEC/'data-dictionary.json').write_text(json.dumps(dictionary,indent=2)+'\n',encoding='utf-8')
print(f'Wrote {len(entities)} logical entities and {len(relations)} relationships')

# Separate, explicitly scoped local bootstrap contract; never part of source acquisition.
bootstrap={'openapi':'3.0.3','info':{'title':'MCPStudio Local Session Bootstrap',
    'version':'0.2.0-review','description':'Host-launcher bootstrap only; loopback and exact-origin gates. Not implemented.'},
    'servers':copy.deepcopy(api['servers']), 'paths':{},
    'components':{'securitySchemes':{'localSession':copy.deepcopy(api['components']['securitySchemes']['localSession'])},
                  'schemas':{'Error':copy.deepcopy(S['Error'])}}}
BS=bootstrap['components']['schemas']
BS['BootstrapExchange']=obj({'one_time_code':string(pattern='^[A-Za-z0-9_-]{43}$'),
    'browser_nonce':string(pattern='^[A-Za-z0-9_-]{43}$')})
BS['LocalSession']=obj({'actor_id':uuid(),'tenant_id':uuid(),'csrf_token':string(minLength=43,maxLength=128),
    'expires_at':time(),'idle_timeout_seconds':integer(enum=[1800]),'absolute_timeout_seconds':integer(enum=[28800])})
for path,method,identifier,response,request in [
    ('/local-session/exchange','post','exchangeBootstrapCode','LocalSession','BootstrapExchange'),
    ('/local-session','get','getLocalSession','LocalSession',None),
    ('/local-session/logout','post','logoutLocalSession',None,None)]:
    o={'operationId':identifier,'summary':identifier,'responses':copy.deepcopy(errors),
       'security':[] if identifier=='exchangeBootstrapCode' else [{'localSession':[]}],
       'parameters':[],'x-semantic-rules':['SEM-BOOTSTRAP']}
    if request:
        o['requestBody']={'required':True,'content':{'application/json':{'schema':ref(request)}}}
    if response:
        o['responses']['200']={'description':'Local operator session; response must use Cache-Control: no-store.',
            'content':{'application/json':{'schema':ref(response)}}}
    else:
        o['responses']['204']={'description':'Session revoked and cookie cleared.'}
    if method=='post':
        o['parameters'].append({'name':'Origin','in':'header','required':True,'schema':string(),
            'description':'Exact trusted loopback frontend origin; null and wildcard forbidden.'})
    if identifier=='logoutLocalSession':
        o['parameters'].append({'name':'X-CSRF-Token','in':'header','required':True,'schema':string(minLength=43)})
    bootstrap['paths'][path]={method:o}
(SPEC/'bootstrap.openapi.yaml').write_text(json.dumps(bootstrap,indent=2)+'\n',encoding='utf-8')
print('Wrote 3 local-session bootstrap contract operations')
