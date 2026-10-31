"""Current seven-migration payload contract/binding integration fixture."""
from pathlib import Path
from copy import deepcopy
import concurrent.futures
import hashlib,json,secrets,subprocess,sys,time,uuid
from datetime import datetime
root=Path(__file__).resolve().parents[3];sys.path[:0]=[str(root/'tools'),str(root/'work/python-tools')]
from plan_payload import canonical_plan_bytes,strict_json
import rfc8785
from jsonschema import RefResolver
from openapi_schema_validator import OAS30Validator
image=json.loads((root/'docs/quality/local-service-images.json').read_text())['images']['postgres']
container='mcpstudio-schema-acceptance-'+uuid.uuid4().hex[:12];checks=[]
def cmd(args,**kw):return subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=60,**kw)
def sql(s,user='postgres'):return cmd(['docker','exec','-i',container,'psql','-U',user,'-d','postgres','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose'],input='SET search_path=pg_catalog,studio_admission,pg_temp;\n'+s)
def check(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise RuntimeError(n)
def good(s,user='postgres'):
 p=sql(s,user)
 if p.returncode:raise RuntimeError(p.stderr)
 return p.stdout.strip()
def reject(n,s,code='23514',user='postgres'):
 p=sql(s,user);check(n,p.returncode!=0 and code in p.stderr)
def U(n):return "'00000000-0000-4000-8000-%012d'"%n
def uid(n):return U(n)[1:-1]
def J(value):return "'"+json.dumps(value,ensure_ascii=True).replace("'","''")+"'::jsonb"
T,A,P,AN,PL,PO,CA=map(U,[1,2,3,4,5,7,8])
versions=[{'id':'tree-sitter','version':'0.26.0'},{'id':'tree-sitter-typescript','version':'0.23.2'}]
evidence=[{'path':'fixture.ts','source_digest':'a'*64,'detector_version':'0.23.2','line_start':1,'line_end':1}]
base_candidate=dict(tenant_id=uid(1),analysis_id=uid(4),id=uid(8),eligible=True,source_reference='fixture.ts:1',graph_node_id=uid(10),
 finding_id='fixture.read',operation_type='read',side_effects=[],sensitivity='internal',required_scopes=['read:fixture'],
 input_schema={'type':'object','properties':{'id':{'type':'string'}},'required':['id'],'additionalProperties':False},
 output_schema={'type':'object','properties':{'value':{'type':'string'}},'required':['value'],'additionalProperties':False},
 eligibility='allowed',reason_codes=[],evidence=evidence,detector=versions[1],provenance='deterministic',
 confidence={'value':None,'method':'fixture structural evidence'},domain_service_reference='fixture.Service.read')
def insert_candidate(c):return f'INSERT INTO candidate SELECT * FROM jsonb_populate_record(NULL::candidate,{J(c)});'
def policy(revision,label,body_changes=None):
 body=dict(id=uid(7),version=label,policy_key='local-default',schema_version='policy.v1',required_checks=['compile'])
 if body_changes:body.update(body_changes)
 wire=rfc8785.dumps(body)
 return f"INSERT INTO validation_policy(tenant_id,id,version,required_checks,version_label,policy_key,schema_version,canonical_content) VALUES({T},{PO},{revision},ARRAY['compile'],'{label}','local-default','policy.v1',decode('{wire.hex()}','hex'));"
def payload():
 return dict(snapshot_id=uid(9),source_digest='a'*64,analysis_id=uid(4),analyzer_versions=deepcopy(versions),recommendation_id=uid(12),recommendation_version=1,
 selected_type='server',candidates=[{k:deepcopy(base_candidate[k]) for k in ['id','input_schema','output_schema','domain_service_reference','required_scopes']}],
 generator={'id':'fixture-generator','version':'0.1.0'},configuration={'plugin':{'id':'fixture-plugin','version':'0.1.0'},
 'schema':{'id':'fixture-config','version':'1'},'values':{'service_name':'fixture','timeout_ms':1000,'arguments':['--first','--second']}},
 transport='stdio',policy={'id':uid(7),'version':'2026.10+local','required_checks':['compile']},override_reason=None)
def publish(n,body,revision=1,validate=True):
 wire=canonical_plan_bytes(body) if validate else rfc8785.dumps(body)
 sha=hashlib.sha256(wire).hexdigest()
 return f"SELECT new_plan({T},{AN},{U(n)},'{sha}'::digest,{U(12)},1);INSERT INTO plan_binding VALUES({T},{U(n)},{PO},{revision},decode('{wire.hex()}','hex'),repeat('a',64));"
api=json.loads((root/'packages/contracts/specs/openapi.yaml').read_text())
def conforms(name,data):return not list(OAS30Validator(api['components']['schemas'][name],resolver=RefResolver.from_schema(api),format_checker=OAS30Validator.FORMAT_CHECKER).iter_errors(data))
report={'scope':'Migrations 001-008: physical-field closure and scoped principal/project metadata, plus canonical payload integration; not full application/security acceptance','image':image,'published_ports':False,'passed':False}
try:
 p=cmd(['docker','run','-d','--rm','--name',container,'--network','none','--memory','512m','--cpus','1','--tmpfs','/var/lib/postgresql/data:rw,size=512m','-e','POSTGRES_PASSWORD='+secrets.token_urlsafe(32),image])
 if p.returncode:raise RuntimeError(p.stderr)
 for _ in range(40):
  if cmd(['docker','exec',container,'pg_isready','-U','postgres']).returncode==0:break
  time.sleep(.5)
 migrations=[p.name for p in sorted((root/'infra/database/migrations').glob('*.sql')) if p.name[:3]<='008']
 for filename in migrations:
  good((root/'infra/database/migrations'/filename).read_text());check(filename+' applies',True)
 good(f"INSERT INTO tenant(id,name) VALUES({T},'Fixture workspace'),({U(20)},'Foreign workspace');INSERT INTO actor(id,subject) VALUES({A},'local:fixture-operator'),({U(21)},'local:foreign-operator');INSERT INTO membership(tenant_id,actor_id,active,role) VALUES({T},{A},true,'operator'),({U(20)},{U(21)},true,'operator');INSERT INTO project(tenant_id,id,name,source) VALUES({T},{P},'Fixture project',{J(dict(kind='local',location='C:/fixture/source'))});INSERT INTO source_snapshot(tenant_id,project_id,id,source_digest,storage_key,resolved_revision) VALUES({T},{P},{U(9)},repeat('a',64),'fixture/source','r1');INSERT INTO analysis(tenant_id,project_id,id,source_digest,snapshot_id,resolved_revision,status,completed_at,analyzer_versions) VALUES({T},{P},{AN},repeat('a',64),{U(9)},'r1','succeeded',now(),{J(versions)});INSERT INTO graph_node VALUES({T},{AN},{U(10)},'function','Fixture',{J(evidence)},'deterministic','{{}}');")
 for name,changes in [('model evidence',{'provenance':'model'}),('side effects',{'side_effects':['write']}),('unknown sensitivity',{'sensitivity':'unknown'}),('write operation',{'operation_type':'write'}),('duplicate scopes',{'required_scopes':['read:fixture','read:fixture']}),('empty evidence',{'evidence':[]}),('changed source evidence',{'evidence':[dict(evidence[0],source_digest='b'*64)]}),('eligibility disagreement',{'eligibility':'blocked'})]:
  c=deepcopy(base_candidate);c['id']=uid(40);c.update(changes);reject(name+' cannot create allowed candidate',insert_candidate(c))
 good(insert_candidate(base_candidate))
 c=deepcopy(base_candidate);c.update(id=uid(41),eligible=False,eligibility='blocked',operation_type='write',side_effects=['write'])
 good(insert_candidate(c));check('blocked write candidate stays nonexecutable data',True)
 doc=json.loads(good(f"SELECT to_jsonb(c)-ARRAY['tenant_id','analysis_id','eligible','source_reference','domain_service_reference'] FROM candidate c WHERE id={CA};"))
 check('stored complete candidate conforms to unchanged OpenAPI',conforms('Candidate',doc))
 good(policy(1,'2026.10+local')+policy(2,'01')+policy(3,'1'))
 reject('policy canonical content cannot contradict label',policy(4,'bad',{'version':'different'}))
 reject('policy exact labels cannot alias another revision',policy(4,'01'),'23505')
 reject('policy content is immutable',"UPDATE validation_policy SET policy_key='changed';")
 check('opaque version labels retain leading zero distinction',good("SELECT string_agg(version_label,',' ORDER BY version) FROM validation_policy;")=='2026.10+local,01,1')
 check('policy content hash derives from exact bytes',good("SELECT bool_and(content_hash=encode(sha256(canonical_content),'hex')) FROM validation_policy;")=='t')
 pol=json.loads(good(f"SELECT jsonb_build_object('id',id,'version',version_label,'required_checks',required_checks) FROM validation_policy WHERE id={PO} AND version=1;"))
 check('string policy reference conforms to unchanged OpenAPI',conforms('PolicyReference',pol))
 good(f"INSERT INTO recommendation VALUES({T},{AN},{U(12)},1,repeat('a',64),'server','fixture rationale',ARRAY[{CA}]::uuid[],'[]','[]',true,'fixture supported');")
 body=payload();wire=canonical_plan_bytes(body)
 check('full canonical payload conforms to unchanged OpenAPI',conforms('CanonicalPlan',json.loads(wire)))
 reordered=deepcopy(body);reordered['analyzer_versions'].reverse();check('set normalization stabilizes analyzer ordering',canonical_plan_bytes(reordered)==wire)
 reordered=deepcopy(body);reordered['configuration']['values']['arguments'].reverse();check('ordered configuration arrays retain order',canonical_plan_bytes(reordered)!=wire)
 for name,change in [('duplicate scopes',lambda x:x['candidates'][0]['required_scopes'].append('read:fixture')),('duplicate candidate identity',lambda x:x['candidates'].append(deepcopy(x['candidates'][0]))),('confidence in executable payload',lambda x:x['candidates'][0].update(confidence=.9)),('unsafe integer',lambda x:x['configuration']['values'].update(timeout_ms=2**54)),('nonfinite float',lambda x:x['configuration']['values'].update(threshold=float('nan'))),('malformed Unicode',lambda x:x['configuration']['values'].update(text='\ud800'))]:
  bad=deepcopy(body);change(bad)
  try:canonical_plan_bytes(bad)
  except Exception:check('canonical boundary rejects '+name,True)
  else:check('canonical boundary rejects '+name,False)
 for text in ['{"x":1,"x":2}','{"x":NaN}']:
  try:strict_json(text)
  except ValueError:check('strict JSON boundary rejects '+('duplicate keys' if 'NaN' not in text else 'NaN'),True)
  else:check('strict JSON boundary',False)
 for name,change in [('candidate scopes',lambda x:x['candidates'][0].update(required_scopes=['admin'])),('candidate I/O schema',lambda x:x['candidates'][0].update(input_schema={'type':'string'})),('domain service',lambda x:x['candidates'][0].update(domain_service_reference='other.Service')),('policy checks',lambda x:x['policy'].update(required_checks=['other'])),('policy version coercion',lambda x:x['policy'].update(version='1')),('analyzer pins',lambda x:x['analyzer_versions'][0].update(version='wrong'))]:
  bad=deepcopy(body);change(bad);reject('database rejects changed '+name,'BEGIN;'+publish(50,bad,validate=False))
 good(publish(5,body))
 good(f"CREATE ROLE fixture_payload_backend LOGIN IN ROLE studio_backend;CREATE ROLE fixture_payload_worker LOGIN IN ROLE studio_worker;CREATE ROLE fixture_payload_foreign LOGIN IN ROLE studio_backend;INSERT INTO runtime_principal VALUES('fixture_payload_backend',{T},{A},'backend',true),('fixture_payload_worker',{T},{A},'worker',true),('fixture_payload_foreign',{U(20)},{U(21)},'backend',true);")
 plan_doc=json.loads(good(f"SELECT backend_plan_document({PL});",'fixture_payload_backend'))
 check('scoped draft Plan conforms to unchanged OpenAPI',conforms('Plan',plan_doc))
 check('required canonical override null survives serialization','override_reason' in plan_doc['canonical_payload'] and plan_doc['canonical_payload']['override_reason'] is None)
 reject('foreign tenant cannot fetch plan document',f"SELECT backend_plan_document({PL});",'42501','fixture_payload_foreign')
 reject('worker cannot fetch backend plan document',f"SELECT backend_plan_document({PL});",'42501','fixture_payload_worker')
 reject('plan projection remains private','SELECT * FROM plan_contract;','42501','fixture_payload_backend')
 ap=good(f"SELECT backend_approve_plan({PL},1,'{hashlib.sha256(wire).hexdigest()}',true);",'fixture_payload_backend')
 rid=good(f"SELECT backend_submit({PL},'{ap}','payload',repeat('a',64));",'fixture_payload_backend')
 check('generation pins exact generator reference',json.loads(good(f"SELECT generator FROM run WHERE id='{rid}';"))==body['generator'])
 good(f"INSERT INTO worker_assignment VALUES('fixture_payload_worker',{T},'{rid}',true);")
 data=b'{}\n';entry={'path':'package.json','sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data)};manifest=rfc8785.dumps([entry])
 good(f"SELECT worker_artifact('{rid}',{U(60)},'package.json','fixture/package','{entry['sha256']}','application/json',{entry['size_bytes']});SELECT worker_publish('{rid}','{hashlib.sha256(manifest).hexdigest()}',decode('{manifest.hex()}','hex'));",'fixture_payload_worker')
 vid=good(f"SELECT backend_validate('{rid}');",'fixture_payload_backend')
 check('validation reference preserves exact opaque policy label',good(f"SELECT policy_version FROM validation_policy_reference WHERE validation_id='{vid}';")=='2026.10+local')
 good(f"SELECT worker_check('{vid}','compile','passed','fixture-check','fixture-v1',0,now(),now(),'fixture-log',NULL);SELECT worker_finish_validation('{vid}');",'fixture_payload_worker')
 check('full payload plan reaches gated export through scoped roles',bool(good(f"SELECT backend_export('{vid}');",'fixture_payload_backend')))
 plan_doc=json.loads(good(f"SELECT backend_plan_document({PL});",'fixture_payload_backend'));check('approved Plan still conforms to unchanged OpenAPI',conforms('Plan',plan_doc) and plan_doc['status']=='approved')
 for n,(name,change) in enumerate([('configuration values',lambda x:x['configuration']['values'].update(timeout_ms=2000)),('plugin pin',lambda x:x['configuration']['plugin'].update(version='0.2.0')),('configuration schema pin',lambda x:x['configuration']['schema'].update(version='2')),('generator pin',lambda x:x['generator'].update(version='0.2.0'))],70):
  changed=deepcopy(body);change(changed);good(publish(n,changed))
  reject('old approval cannot authorize changed '+name,f"SELECT backend_submit({U(n)},'{ap}','changed-{n}',repeat('a',64));",user='fixture_payload_backend')
  check(name+' changes canonical digest',hashlib.sha256(canonical_plan_bytes(changed)).hexdigest()!=hashlib.sha256(wire).hexdigest())
 changed=deepcopy(body);changed['policy']['version']='01';good(publish(80,changed,revision=2))
 document=json.loads(good(f"SELECT backend_plan_document({U(80)});",'fixture_payload_backend'))
 check('opaque policy label projects without integer coercion',document['policy_version']=='01' and document['canonical_payload']['policy']['version']=='01' and conforms('Plan',document))
 reject('old approval cannot authorize new policy version',f"SELECT backend_submit({U(80)},'{ap}','changed-policy',repeat('a',64));",user='fixture_payload_backend')
 catalog=json.loads(good("SELECT json_agg(json_build_object('table',table_name,'column',column_name,'type',data_type,'nullable',is_nullable) ORDER BY table_name,ordinal_position) FROM information_schema.columns WHERE table_schema='studio_admission';"))
 (root/'docs/quality/physical-schema-catalog.json').write_text(json.dumps({'scope':'Actual catalog after migrations 001-008 in payload-chain fixture','columns':catalog,'migration_files':migrations},indent=2)+'\n',encoding='utf-8')

 metadata=json.loads(good(f"SELECT backend_project_metadata({P});",'fixture_payload_backend'))
 check('scoped project Source matches unchanged API schema',conforms('Source',metadata['source']))
 check('project input metadata matches unchanged API schema',conforms('ProjectInput',{'name':metadata['name'],'source':metadata['source']}))
 check('project timestamps are ordered timezone-aware values',datetime.fromisoformat(metadata['updated_at'])>=datetime.fromisoformat(metadata['created_at']) and datetime.fromisoformat(metadata['created_at']).tzinfo is not None)
 reject('blank workspace name rejected',f"INSERT INTO tenant(id,name) VALUES({U(90)},' ');")
 reject('blank principal subject rejected',f"INSERT INTO actor(id,subject) VALUES({U(90)},' ');")
 reject('duplicate principal subject rejected',f"INSERT INTO actor(id,subject) VALUES({U(90)},'local:fixture-operator');",'23505')
 reject('principal subject cannot be rebound',f"UPDATE actor SET subject='other' WHERE id={A};")
 reject('principal identity cannot be deleted',f"DELETE FROM actor WHERE id={A};")
 reject('unsupported membership role rejected',f"INSERT INTO membership(tenant_id,actor_id,active,role) VALUES({T},{U(21)},true,'owner');")
 reject('existing operator cannot be changed to unsupported role',f"UPDATE membership SET role='admin' WHERE tenant_id={T} AND actor_id={A};")
 def project_insert(n,name,source):
  return f"INSERT INTO project(tenant_id,id,name,source) VALUES({T},{U(n)},'{name}',{J(source)});"
 good_source={'kind':'local','location':'C:/fixture/source'}
 reject('blank project name rejected',project_insert(91,' ',good_source))
 reject('oversized project name rejected',project_insert(91,'x'*201,good_source))
 sources=[('unknown source fields',dict(good_source,password='fixture-canary')),('missing source kind',{'location':'C:/fixture/source'}),
 ('unsupported source kind',{'kind':'cloud','location':'fixture'}),('blank source location',dict(good_source,location=' ')),
 ('git missing revision',{'kind':'git','location':'https://example.invalid/repo.git'}),('null source revision',dict(good_source,revision=None)),
 ('null credential reference',dict(good_source,credential_reference=None)),('nonstring revision',dict(good_source,revision=7)),
 ('inline URL credentials',{'kind':'git','location':'https://user:fixture-canary@example.invalid/repo.git','revision':'main'}),
 ('obvious credential query',{'kind':'git','location':'https://example.invalid/repo.git?token=fixture-canary','revision':'main'})]
 for name,source in sources:reject(name+' rejected',project_insert(91,'Invalid source fixture',source))
 git_source={'kind':'git','location':'https://example.invalid/repo.git','revision':'main','credential_reference':'fixture-opaque-reference'}
 good(project_insert(92,'Git metadata fixture',git_source))
 git=json.loads(good(f"SELECT backend_project_metadata({U(92)});",'fixture_payload_backend'))
 check('git source with opaque reference matches API schema',conforms('Source',git['source']) and git['source']==git_source)
 reject('project source cannot be silently replaced',f"UPDATE project SET source={J(dict(kind='local',location='C:/other'))} WHERE id={P};")
 reject('project creation timestamp immutable',f"UPDATE project SET created_at='1970-01-01T00:00:00Z' WHERE id={P};")
 reject('project tenant identity immutable',f"UPDATE project SET tenant_id={U(20)} WHERE id={P};")
 good(f"UPDATE project SET name='Renamed fixture',updated_at='1970-01-01T00:00:00Z' WHERE id={P};")
 renamed=json.loads(good(f"SELECT backend_project_metadata({P});",'fixture_payload_backend'))
 check('project update timestamp is server-maintained',renamed['created_at']==metadata['created_at'] and datetime.fromisoformat(renamed['updated_at'])>=datetime.fromisoformat(metadata['updated_at']) and renamed['name']=='Renamed fixture')
 reject('foreign tenant cannot read project metadata',f"SELECT backend_project_metadata({P});",'42501','fixture_payload_foreign')
 reject('worker cannot invoke backend metadata reader',f"SELECT backend_project_metadata({P});",'42501','fixture_payload_worker')
 reject('backend has no raw principal writes',f"UPDATE actor SET subject='forged' WHERE id={A};",'42501','fixture_payload_backend')
 reject('worker cannot change its membership role',"UPDATE membership SET role='operator';",'42501','fixture_payload_worker')
 reject('backend still cannot read raw projects','SELECT * FROM project;','42501','fixture_payload_backend')
 good(f"UPDATE membership SET active=false WHERE tenant_id={T} AND actor_id={A};")
 reject('deactivated operator loses metadata access',f"SELECT backend_project_metadata({P});",'42501','fixture_payload_backend')
 good(f"UPDATE membership SET active=true WHERE tenant_id={T} AND actor_id={A};")
 check('metadata audit retains source contents outside event record',good("SELECT count(*) FROM audit_event WHERE entity='project' AND (entity_key ? 'source' OR entity_key ? 'location');")=='0')
 current=json.loads(good(f"SELECT backend_plan_document({U(80)});",'fixture_payload_backend'))
 current_approval=good(f"SELECT backend_approve_plan({U(80)},{current['version']},'{current['content_hash']}',true);",'fixture_payload_backend')
 with concurrent.futures.ThreadPoolExecutor(2) as pool:
  admitted=list(pool.map(lambda _:good(f"SELECT backend_submit({U(80)},'{current_approval}','current-concurrent',repeat('a',64));",'fixture_payload_backend'),range(2)))
 check('current full-payload concurrent requests admit one run',len(set(admitted))==1)
 current_run=admitted[0]
 check('current concurrent admission creates one outbox identity',good(f"SELECT count(*) FROM outbox WHERE run_id='{current_run}';")=='1')
 queued_run=good(f"SELECT backend_submit({U(80)},'{current_approval}','queued-before-revoke',repeat('a',64));",'fixture_payload_backend')
 good(f"INSERT INTO worker_assignment VALUES('fixture_payload_worker',{T},'{current_run}',true),('fixture_payload_worker',{T},'{queued_run}',true);")
 good(f"SELECT worker_artifact('{current_run}',{U(160)},'package.json','fixture/package','{entry['sha256']}','application/json',{entry['size_bytes']});SELECT worker_publish('{current_run}','{hashlib.sha256(manifest).hexdigest()}',decode('{manifest.hex()}','hex'));",'fixture_payload_worker')
 current_validation=good(f"SELECT backend_validate('{current_run}');",'fixture_payload_backend')
 good(f"SELECT worker_check('{current_validation}','compile','passed','fixture-check','fixture-v1',0,now(),now(),'fixture-log',NULL);SELECT worker_finish_validation('{current_validation}');",'fixture_payload_worker')
 check('current validation preserves leading-zero policy label',good(f"SELECT policy_version FROM validation_policy_reference WHERE validation_id='{current_validation}';")=='01')
 with concurrent.futures.ThreadPoolExecutor(3) as pool:
  revoking=pool.submit(good,f"SET application_name='schema-final-revoke';BEGIN;SELECT backend_revoke_plan({U(80)},'current schema acceptance race');SELECT pg_sleep(3);COMMIT;",'fixture_payload_backend')
  observed=False
  for _ in range(60):
   if good("SELECT count(*) FROM pg_stat_activity WHERE application_name='schema-final-revoke' AND wait_event='PgSleep';")=='1':observed=True;break
   time.sleep(.02)
  check('current revocation transaction is observed',observed)
  admitting=pool.submit(sql,f"SELECT backend_submit({U(80)},'{current_approval}','during-revocation',repeat('a',64));",'fixture_payload_backend')
  exporting=pool.submit(sql,f"SELECT backend_export('{current_validation}');",'fixture_payload_backend')
  waiting=False
  for _ in range(40):
   if int(good('SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid))>0;'))>=2:waiting=True;break
   time.sleep(.02)
  check('current admission and export wait behind revocation',waiting)
  revoking.result();admit_result=admitting.result();export_result=exporting.result()
  check('current committed revocation rejects queued admission',admit_result.returncode!=0 and 'plan explicitly revoked' in admit_result.stderr)
  check('current committed revocation rejects export',export_result.returncode!=0 and 'plan explicitly revoked' in export_result.stderr)
 rejected_publish=sql(f"SELECT worker_publish('{queued_run}','{hashlib.sha256(manifest).hexdigest()}',decode('{manifest.hex()}','hex'));",'fixture_payload_worker')
 check('current revocation blocks assigned unfinished publication',rejected_publish.returncode!=0 and 'plan explicitly revoked' in rejected_publish.stderr)
 check('rejected publication leaves queued run unchanged',good(f"SELECT backend_run_status('{queued_run}');",'fixture_payload_backend')=='queued')
 good(f"INSERT INTO analysis(tenant_id,project_id,id,source_digest,snapshot_id,resolved_revision,status,completed_at,analyzer_versions) VALUES({T},{P},{U(170)},repeat('a',64),{U(9)},'r1','succeeded',now(),{J(versions)});INSERT INTO graph_node VALUES({T},{U(170)},{U(171)},'function','Second analysis fixture',{J(evidence)},'deterministic','{{}}');")
 reused=deepcopy(base_candidate);reused.update(analysis_id=uid(170),graph_node_id=uid(171))
 reject('candidate UUID cannot be reused across analyses in one tenant',insert_candidate(reused),'23505')
 catalog=json.loads(good("SELECT json_agg(json_build_object('table',table_name,'column',column_name,'type',data_type,'nullable',is_nullable) ORDER BY table_name,ordinal_position) FROM information_schema.columns WHERE table_schema='studio_admission';"))
 (root/'docs/quality/physical-schema-catalog.json').write_text(json.dumps({'scope':'Actual catalog after migrations 001-008 in schema-acceptance fixture','columns':catalog,'migration_files':migrations},indent=2)+'\n',encoding='utf-8')

 report['passed']=True
except Exception as ex:report['error']=str(ex)
finally:
 cmd(['docker','rm','--force',container]);report['fixture_removed']=cmd(['docker','inspect',container]).returncode!=0
 report['passed']=report['passed'] and report['fixture_removed'];report['checks']=checks
 (root/'docs/quality/schema-acceptance-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
