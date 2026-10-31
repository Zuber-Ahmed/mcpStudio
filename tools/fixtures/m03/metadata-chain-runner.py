"""Ownership-chain regression and real-login smoke test across migrations 001-006."""
from pathlib import Path
import concurrent.futures,hashlib,json,secrets,subprocess,sys,time,uuid
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'work/python-tools'))
import rfc8785
from openapi_schema_validator import OAS30Validator
image=json.loads((root/'docs/quality/local-service-images.json').read_text())['images']['postgres']
container='mcpstudio-metadata-'+uuid.uuid4().hex[:12];checks=[]
def cmd(args,**kw):return subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=60,**kw)
def sql(s,user='postgres'):
 return cmd(['docker','exec','-i',container,'psql','-U',user,'-d','postgres','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose'],input='SET search_path=pg_catalog,studio_admission,pg_temp;\n'+s)
def check(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise RuntimeError(n)
def good(s,user='postgres'):
 p=sql(s,user)
 if p.returncode:raise RuntimeError(p.stderr)
 return p.stdout.strip()
def reject(n,s,code='23514',user='postgres'):
 p=sql(s,user);check(n,p.returncode!=0 and code in p.stderr)
def uid(n):return '00000000-0000-4000-8000-%012d'%n
def U(n):return "'"+uid(n)+"'"
T,A,P,AN,PL,AP,PO,CA=map(U,range(1,9))
def analysis(n,project=P,snapshot=U(9),tenant=T,digest="repeat('a',64)",revision="'fixture-r1'",status='succeeded',previous='NULL'):
 return f"INSERT INTO analysis(tenant_id,project_id,id,source_digest,snapshot_id,resolved_revision,status,completed_at,previous_run_id) VALUES({tenant},{project},{U(n)},{digest},{snapshot},{revision},'{status}',"+('now()' if status=='succeeded' else 'NULL')+f',{previous});'
def node(n,an=AN,tenant=T,evidence="'[{\"path\":\"fixture.ts\",\"line\":1}]'"):
 return f"INSERT INTO graph_node VALUES({tenant},{an},{U(n)},'function','Fixture',{evidence}::jsonb,'fixture-deterministic','{{}}');"
def rec(n,version=1,ids=None,an=AN,digest="repeat('a',64)",supported=True,kind='server'):
 ids=ids if ids is not None else [CA]
 array='ARRAY['+','.join(ids)+']::uuid[]'
 return f"INSERT INTO recommendation VALUES({T},{an},{U(n)},{version},{digest},'{kind}','fixture rationale',{array},'[]','[]',{str(supported).lower()},'fixture availability');"
def payload(**changes):
 d=dict(analysis_id=uid(4),source_digest='a'*64,snapshot_id=uid(9),recommendation_id=uid(12),recommendation_version=1,
  policy_id=uid(7),policy_version=1,candidate_ids=[uid(8)],mode='server',transport='stdio');d.update(changes)
 return rfc8785.dumps(d)
def publish(n,body,rec_id=U(12),rec_version=1,an=AN):
 h=hashlib.sha256(body).hexdigest()
 return f"SELECT new_plan({T},{an},{U(n)},'{h}'::digest,{rec_id},{rec_version});INSERT INTO plan_binding VALUES({T},{U(n)},{PO},1,decode('{body.hex()}','hex'),repeat('a',64));"
report={'scope':'Migrations 001-006: identity/approval/durable metadata and OpenAPI response checks; includes prior chain integration, no live service database or API implementation','image':image,'published_ports':False,'passed':False}
try:
 p=cmd(['docker','run','-d','--rm','--name',container,'--network','none','--memory','512m','--cpus','1','--tmpfs','/var/lib/postgresql/data:rw,size=512m','-e','POSTGRES_PASSWORD='+secrets.token_urlsafe(32),image])
 if p.returncode:raise RuntimeError(p.stderr)
 for _ in range(40):
  if cmd(['docker','exec',container,'pg_isready','-U','postgres']).returncode==0:break
  time.sleep(.5)
 migrations=['001_admission_kernel.sql','002_bound_validation.sql','003_runtime_roles.sql','004_source_graph_recommendation.sql','005_artifacts_findings_revocations.sql','006_identity_approval_metadata.sql']
 for filename in migrations:
  good((root/'infra/database/migrations'/filename).read_text());check(filename+' applies',True)
 good(f"INSERT INTO tenant VALUES({T}),({U(20)});INSERT INTO actor VALUES({A});INSERT INTO membership VALUES({T},{A},true);INSERT INTO project VALUES({T},{P}),({T},{U(21)}),({U(20)},{U(22)});")
 good(f"INSERT INTO source_snapshot(tenant_id,project_id,id,source_digest,storage_key,resolved_revision) VALUES({T},{P},{U(9)},repeat('a',64),'fixture/source','fixture-r1'),({T},{U(21)},{U(23)},repeat('b',64),'fixture/other','fixture-r2'),({U(20)},{U(22)},{U(24)},repeat('c',64),'fixture/foreign','fixture-r3');")
 good(analysis(4)+analysis(25)+analysis(26,status='queued')+analysis(27,project=U(21),snapshot=U(23),digest="repeat('b',64)",revision="'fixture-r2'"))
 check('analysis pins exact source snapshot identity',True)
 for name,options in [('foreign tenant snapshot',{'snapshot':U(24)}),('foreign project snapshot',{'snapshot':U(23),'digest':"repeat('b',64)",'revision':"'fixture-r2'"}),('changed source digest',{'digest':"repeat('b',64)"}),('changed resolved revision',{'revision':"'wrong'"})]:
  reject(name+' denied',analysis(30,**options),'23503')
 reject('snapshot mutation denied',"UPDATE source_snapshot SET storage_key='changed';")
 reject('snapshot deletion denied','DELETE FROM source_snapshot;')
 reject('terminal analysis reopening denied',f"UPDATE analysis SET status='running',completed_at=NULL WHERE id={AN};")
 reject('analysis source replacement denied',f"UPDATE analysis SET snapshot_id={U(23)} WHERE id={AN};")
 reject('foreign project predecessor denied',analysis(30,previous=U(27)),'23503')
 good(node(10)+node(11,an=U(25)))
 reject('empty graph evidence denied',node(30,evidence="'[]'"))
 good(f"INSERT INTO graph_edge VALUES({T},{AN},{U(31)},{U(10)},{U(10)},'self','fixture','[{{\"path\":\"fixture.ts\"}}]');")
 reject('cross-analysis edge denied',f"INSERT INTO graph_edge VALUES({T},{AN},{U(32)},{U(10)},{U(11)},'call','fixture','[{{\"path\":\"fixture.ts\"}}]');",'23503')
 reject('cross-tenant graph node denied',node(32,tenant=U(20)),'23503')
 reject('graph evidence mutation denied',"UPDATE graph_node SET label='forged';")
 good(f"INSERT INTO candidate VALUES({T},{AN},{CA},true,'fixture.ts:1',{U(10)}),({T},{U(25)},{U(33)},true,'other.ts:1',{U(11)}),({T},{AN},{U(34)},true,'fixture.ts:2',{U(10)}),({T},{AN},{U(35)},false,'fixture.ts:3',{U(10)});")
 reject('candidate foreign-analysis node denied',f"INSERT INTO candidate VALUES({T},{AN},{U(36)},true,'fixture.ts:1',{U(11)});",'23503')
 reject('candidate foreign-tenant node denied',f"INSERT INTO candidate VALUES({U(20)},{AN},{U(36)},true,'fixture.ts:1',{U(10)});",'23503')
 for name,opts in [('foreign candidate',{'ids':[U(33)]}),('duplicate candidate',{'ids':[CA,CA]}),('ineligible candidate',{'ids':[U(35)]}),('empty executable candidates',{'ids':[]}),('unsupported executable type',{'kind':'client'}),('unfinished analysis',{'an':U(26),'ids':[],'supported':False,'kind':'none'})]:reject(name+' recommendation denied',rec(40,**opts))
 reject('recommendation changed source denied',rec(40,digest="repeat('b',64)"),'23503')
 good(rec(12));check('eligible source-bound recommendation accepted',True)
 reject('recommendation immutable',"UPDATE recommendation SET rationale='forged';")
 reject('recommendation version gap denied',rec(41,version=3))
 good(rec(41,version=2,ids=[],supported=False,kind='none'));check('explicit none recommendation remains inspectable',True)
 reject('non-generating recommendation cannot produce plan',publish(42,payload(),rec_id=U(41),rec_version=2))
 good(f"INSERT INTO validation_policy VALUES({T},{PO},1,ARRAY['compile']);")
 reject('legacy plan signature fails closed',f"SELECT new_plan({T},{AN},{PL},repeat('a',64)::digest);")
 for name,changes in [('wrong snapshot',{'snapshot_id':uid(23)}),('wrong recommendation',{'recommendation_id':uid(41)}),('wrong recommendation version',{'recommendation_version':2}),('candidate outside recommendation',{'candidate_ids':[uid(34)]}),('changed policy binding',{'policy_version':2})]:reject(name+' payload denied','BEGIN;'+publish(44,payload(**changes)))
 good(publish(5,payload()));check('plan binds snapshot recommendation and exact selected candidates',True)
 good(f"INSERT INTO approval(tenant_id,id,plan_id,actor_id,plan_hash,revoked_at,plan_version,security_confirmed) VALUES({T},{AP},{PL},{A},'{hashlib.sha256(payload()).hexdigest()}',NULL,1,true);CREATE ROLE fixture_source_backend LOGIN IN ROLE studio_backend;CREATE ROLE fixture_source_worker LOGIN IN ROLE studio_worker;INSERT INTO runtime_principal VALUES('fixture_source_backend',{T},{A},'backend',true),('fixture_source_worker',{T},{A},'worker',true);")

 api=json.loads((root/'packages/contracts/specs/openapi.yaml').read_text(encoding='utf-8'))
 def conforms(name,document):
  validator=OAS30Validator(api['components']['schemas'][name],format_checker=OAS30Validator.FORMAT_CHECKER)
  return not list(validator.iter_errors(document))
 approval_hash=hashlib.sha256(payload()).hexdigest()
 reject('approval rejects wrong explicit plan version',f"SELECT backend_approve_plan({PL},2,'{approval_hash}',true);",user='fixture_source_backend')
 reject('approval rejects wrong explicit plan hash',f"SELECT backend_approve_plan({PL},1,repeat('b',64),true);",user='fixture_source_backend')
 reject('approval requires affirmative security confirmation',f"SELECT backend_approve_plan({PL},1,'{approval_hash}',false);",user='fixture_source_backend')
 reject('approval rejects null security confirmation',f"SELECT backend_approve_plan({PL},1,'{approval_hash}',NULL);",user='fixture_source_backend')
 approval_id=good(f"SELECT backend_approve_plan({PL},1,'{approval_hash}',true);",'fixture_source_backend')
 doc=json.loads(good(f"SELECT to_jsonb(a)-'tenant_id' FROM approval a WHERE id='{approval_id}';"))
 check('stored scoped approval conforms to current OpenAPI',conforms('Approval',doc))
 check('approval records have explicit security version and timestamp',doc['security_confirmed'] and doc['plan_version']==1 and bool(doc['approved_at']))
 reject('approval confirmation cannot be edited',f"UPDATE approval SET security_confirmed=false WHERE id='{approval_id}';")
 reject('worker cannot approve a plan',f"SELECT backend_approve_plan({PL},1,'{approval_hash}',true);",'42501','fixture_source_worker')

 rid=good(f"SELECT backend_submit({PL},{AP},'source-chain',repeat('a',64));",'fixture_source_backend');check('scoped backend admits fully linked plan',bool(rid))
 good(f"INSERT INTO worker_assignment VALUES('fixture_source_worker',{T},'{rid}',true);")

 # Artifact metadata is derived from these trusted fixture bytes. No remote objects are claimed.
 fixture_files={'package.json':b'{}\n','src/index.ts':b'export {};\n'}
 entries=[{'path':p,'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data)} for p,data in sorted(fixture_files.items())]
 def add_artifact(n,path,sha='a'*64,size=1):
  quoted=path.replace("'","''")
  return f"SELECT worker_artifact('{rid}',{U(n)},'{quoted}','fixture/{n}','{sha}','text/plain',{size});"
 for index,entry in enumerate(entries):good(add_artifact(100+index,entry['path'],entry['sha256'],entry['size_bytes']),'fixture_source_worker')
 check('assigned worker records portable artifact metadata',True)
 bad_paths=['/escape','C:/escape','../escape','a//b','a/./b','a/../b','a\\b','a/NUL.txt','COM1','LPT9.log','CON .txt','a/name.','a/name ','a/%2e%2e/b','https://x','\\\\server\\share','a/na:me','a/'+chr(0x202e)+'.txt','a'*241]
 for path in bad_paths:reject('unsafe artifact path '+repr(path)+' denied',add_artifact(110,path),user='fixture_source_worker')
 reject('case-folded artifact collision denied',add_artifact(110,'SRC/INDEX.ts'),'23505','fixture_source_worker')
 reject('negative artifact size denied',add_artifact(110,'negative.ts',size=-1),user='fixture_source_worker')
 reject('artifact metadata mutation denied',"UPDATE artifact SET sha256=repeat('f',64);")
 def publish_manifest(items,digest=None):
  manifest=rfc8785.dumps(items)
  sha=digest or hashlib.sha256(manifest).hexdigest()
  return f"SELECT worker_publish('{rid}','{sha}',decode('{manifest.hex()}','hex'));"
 reject('legacy digest-only publication fails closed',f"SELECT worker_publish('{rid}',repeat('e',64));",user='fixture_source_worker')
 reject('manifest digest mismatch denied',publish_manifest(entries,'f'*64),user='fixture_source_worker')
 reject('empty manifest denied',publish_manifest([]),user='fixture_source_worker')
 reject('manifest missing artifact denied',publish_manifest(entries[:1]),user='fixture_source_worker')
 reject('manifest order mismatch denied',publish_manifest(list(reversed(entries))),user='fixture_source_worker')
 changed=[dict(e) for e in entries];changed[0]['size_bytes']+=1
 reject('manifest changed artifact descriptor denied',publish_manifest(changed),user='fixture_source_worker')
 check('failed publication leaves generation queued',good(f"SELECT backend_run_status('{rid}');",'fixture_source_backend')=='queued')
 check('failed publication leaves no artifact set',good('SELECT count(*) FROM artifact_set;')=='0')
 good(publish_manifest(entries),'fixture_source_worker');check('exact manifest bytes bind published artifact set',True)
 reject('artifact cannot be appended after publication',add_artifact(110,'late.ts'),user='fixture_source_worker')

 vid=good(f"SELECT backend_validate('{rid}');",'fixture_source_backend')

 other_run=good(f"SELECT backend_submit({PL},{AP},'other-run',repeat('a',64));",'fixture_source_backend')
 good(f"INSERT INTO finding VALUES({T},{U(120)},'{rid}','fixture.warning','warning','fixture','Trusted fixture finding','[]'),({T},{U(121)},'{other_run}','fixture.warning','warning','fixture','Other run finding','[]');")
 reject('duplicate finding stable identity denied',f"INSERT INTO finding VALUES({T},{U(122)},'{rid}','fixture.warning','warning','fixture','Duplicate','[]');",'23505')
 reject('foreign-tenant finding run denied',f"INSERT INTO finding VALUES({U(20)},{U(122)},'{rid}','other','warning','fixture','Foreign','[]');",'23503')
 reject('finding evidence mutation denied',"UPDATE finding SET message='forged';")
 reject('cross-run finding check link denied',f"INSERT INTO validation_check_finding VALUES({T},'{vid}','compile','{rid}',{U(121)});",'23503')
 good(f"INSERT INTO validation_check_finding VALUES({T},'{vid}','compile','{rid}',{U(120)});")
 check('same-run validation finding link accepted',True)
 reject('worker cannot forge finding raw rows',f"INSERT INTO finding VALUES({T},{U(122)},'{rid}','raw','warning','fixture','Raw','[]');",'42501','fixture_source_worker')

 good(f"SELECT worker_check('{vid}','compile','passed','fixture-check','fixture-v1',0,now(),now(),'fixture-log',NULL);SELECT worker_finish_validation('{vid}');",'fixture_source_worker')
 check('complete scoped chain permits guarded export',bool(good(f"SELECT backend_export('{vid}');",'fixture_source_backend')))
 reject('runtime cannot insert source snapshots',f"INSERT INTO source_snapshot(tenant_id,project_id,id,source_digest,storage_key,resolved_revision) VALUES({T},{P},{U(60)},repeat('a',64),'fake','fake');",'42501','fixture_source_backend')
 reject('worker cannot forge graph data',node(60),'42501','fixture_source_worker')
 reject('runtime cannot publish recommendation',rec(60,version=3),'42501','fixture_source_backend')
 # Both sessions request the same next recommendation revision: only one can commit.
 with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda n:sql(rec(n,version=3)),[61,62]))
 check('concurrent same-version recommendations commit once',sum(p.returncode==0 for p in results)==1 and any('23514' in p.stderr for p in results if p.returncode))
 check('recommendation revisions remain contiguous',good('SELECT string_agg(version::text,\',\' ORDER BY version) FROM recommendation;')=='1,2,3')
 check('snapshot and recommendation audit entries exist',good("SELECT count(DISTINCT entity) FROM audit_event WHERE entity IN ('source_snapshot','recommendation');")=='2')
 check('new source tables owned by private owner',good("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='studio_admission' AND c.relname IN ('source_snapshot','graph_node','graph_edge','recommendation') AND c.relowner <> 'studio_kernel_owner'::regrole;")=='0')
 catalog=json.loads(good("SELECT json_agg(json_build_object('table',table_name,'column',column_name,'type',data_type,'nullable',is_nullable) ORDER BY table_name,ordinal_position) FROM information_schema.columns WHERE table_schema='studio_admission';"))
 (root/'docs/quality/physical-schema-catalog.json').write_text(json.dumps({'scope':'Actual PostgreSQL catalog after migrations 001-006 in source-chain fixture','columns':catalog,'migration_files':migrations},indent=2)+'\n',encoding='utf-8')

 reject('finalized validation finding links cannot be appended',f"INSERT INTO validation_check_finding VALUES({T},'{vid}','compile','{rid}',{U(120)});")
 reject('worker cannot revoke plans',f"SELECT backend_revoke_plan({PL},'worker attempt');",'42501','fixture_source_worker')
 reject('blank revocation reason denied',f"SELECT backend_revoke_plan({PL},' ');",user='fixture_source_backend')
 good(f"CREATE ROLE fixture_artifact_foreign LOGIN IN ROLE studio_backend;INSERT INTO actor VALUES({U(130)});INSERT INTO membership VALUES({U(20)},{U(130)},true);INSERT INTO runtime_principal VALUES('fixture_artifact_foreign',{U(20)},{U(130)},'backend',true);")
 reject('foreign tenant cannot revoke plan',f"SELECT backend_revoke_plan({PL},'foreign');",'42501','fixture_artifact_foreign')
 with concurrent.futures.ThreadPoolExecutor(2) as pool:
  future=pool.submit(good,f"SET application_name='explicit-plan-revoke';BEGIN;SELECT backend_revoke_plan({PL},'fixture explicit revocation');SELECT pg_sleep(3);COMMIT;",'fixture_source_backend')
  seen=False
  for _ in range(60):
   if good("SELECT count(*) FROM pg_stat_activity WHERE application_name='explicit-plan-revoke' AND wait_event='PgSleep';")=='1':seen=True;break
   time.sleep(.02)
  check('explicit plan revocation transaction observed',seen)
  attempt=pool.submit(sql,f"SELECT backend_export('{vid}');",'fixture_source_backend');blocked=False
  for _ in range(40):
   if good('SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid))>0;')!='0':blocked=True;break
   time.sleep(.02)
  check('export waits behind explicit plan revocation',blocked)
  future.result();response=attempt.result()
  check('committed plan revocation blocks export',response.returncode!=0 and 'plan explicitly revoked' in response.stderr)
 reject('revoked plan blocks new admission',f"SELECT backend_submit({PL},{AP},'revoked',repeat('a',64));",user='fixture_source_backend')
 reject('revoked plan blocks old idempotent replay',f"SELECT backend_submit({PL},{AP},'source-chain',repeat('a',64));",user='fixture_source_backend')
 good(f"INSERT INTO worker_assignment VALUES('fixture_source_worker',{T},'{other_run}',true);")
 response=sql(f"SELECT worker_publish('{other_run}',repeat('e',64),decode('5b5d','hex'));",'fixture_source_worker')
 check('revoked plan prevents assigned worker publication',response.returncode!=0 and 'plan explicitly revoked' in response.stderr)
 reject('revocation cannot be edited',"UPDATE plan_revocation SET reason='changed';")
 reject('revocation cannot be removed','DELETE FROM plan_revocation;')
 check('explicit revocation creates transactional audit event',good("SELECT count(*) FROM audit_event WHERE entity='plan_revocation';")=='1')
 catalog=json.loads(good("SELECT json_agg(json_build_object('table',table_name,'column',column_name,'type',data_type,'nullable',is_nullable) ORDER BY table_name,ordinal_position) FROM information_schema.columns WHERE table_schema='studio_admission';"))
 (root/'docs/quality/physical-schema-catalog.json').write_text(json.dumps({'scope':'Actual PostgreSQL catalog after migrations 001-006 in artifact-chain fixture','columns':catalog,'migration_files':migrations},indent=2)+'\n',encoding='utf-8')


 check('audit event IDs use UUID storage',good("SELECT data_type FROM information_schema.columns WHERE table_schema='studio_admission' AND table_name='audit_event' AND column_name='id';")=='uuid')
 check('audit ordinal remains separate from external UUID',good("SELECT count(*) FROM information_schema.columns WHERE table_schema='studio_admission' AND table_name='audit_event' AND column_name='sequence_no';")=='1')
 check('runtime audit is attributed to authenticated actor',good(f"SELECT count(*) FROM audit_event WHERE entity='export_record' AND actor_id={A} AND resource_id IS NOT NULL;")=='1')
 check('administrative audit retains explicit unknown actor',good("SELECT count(*) FROM audit_event WHERE entity='source_snapshot' AND actor_id IS NULL;")!='0')
 checks_doc=json.loads(good(f"SELECT backend_validation_checks('{vid}');",'fixture_source_backend'))
 check('scoped check projection conforms to current OpenAPI',all(conforms('Check',c) for c in checks_doc) and bool(checks_doc))
 check('mandatory status derives from pinned policy',all(c['mandatory'] is True for c in checks_doc))
 check('finding links project stable public keys',checks_doc[0]['finding_ids']==['fixture.warning'])
 reject('foreign tenant cannot read check projection',f"SELECT backend_validation_checks('{vid}');",'42501','fixture_artifact_foreign')
 reject('worker cannot read backend check projection',f"SELECT backend_validation_checks('{vid}');",'42501','fixture_source_worker')
 reject('raw contract view remains private','SELECT * FROM validation_check_contract;','42501','fixture_source_backend')
 check('persisted generation hash matches immutable plan',good(f"SELECT (r.plan_hash=p.plan_hash AND r.created_at IS NOT NULL)::text FROM run r JOIN plan p ON p.tenant_id=r.tenant_id AND p.id=r.plan_id WHERE r.id='{rid}';")=='true')
 reject('explicit forged generation hash rejected',f"INSERT INTO run(tenant_id,id,actor_id,plan_id,approval_id,request_digest,plan_hash) VALUES({T},{U(150)},{A},{PL},{AP},repeat('a',64),repeat('b',64));")
 reject('generation cannot reference itself as predecessor',f"INSERT INTO run(tenant_id,id,actor_id,plan_id,approval_id,request_digest,previous_run_id) VALUES({T},{U(150)},{A},{PL},{AP},repeat('a',64),{U(150)});")
 reject('cross-actor generation predecessor rejected',f"INSERT INTO run(tenant_id,id,actor_id,plan_id,approval_id,request_digest,previous_run_id) VALUES({T},{U(150)},{U(130)},{PL},{AP},repeat('a',64),'{rid}');",'23503')
 reject('validation cannot reference itself as predecessor',f"INSERT INTO validation(tenant_id,id,run_id,artifact_digest,policy_id,policy_version,previous_run_id) SELECT tenant_id,{U(151)},run_id,artifact_digest,policy_id,policy_version,{U(151)} FROM validation WHERE id='{vid}';")
 good(f"INSERT INTO validation(tenant_id,id,run_id,artifact_digest,policy_id,policy_version,previous_run_id) SELECT tenant_id,{U(151)},run_id,artifact_digest,policy_id,policy_version,id FROM validation WHERE id='{vid}';")
 pending=json.loads(good(f"SELECT backend_validation_checks({U(151)});",'fixture_source_backend'))
 check('queued check projection omits absent execution metadata',all(conforms('Check',c) and c['status']=='not_run' and 'exit_code' not in c and 'started_at' not in c for c in pending) and bool(pending))
 reject('queued check UUID cannot change',f"UPDATE validation_check SET id=gen_random_uuid() WHERE validation_id={U(151)};")
 check('UUID check identity unique per tenant',good("SELECT count(*)=count(DISTINCT id) FROM validation_check;")=='t')
 outcome=json.loads(good(f"SELECT response FROM idempotency WHERE run_id='{rid}';"))
 check('admission response is durably preserved after run completes',outcome=={'id':rid,'status':'queued'})
 check('idempotency identity metadata is populated',good(f"SELECT (id IS NOT NULL AND created_at IS NOT NULL AND status='admitted')::text FROM idempotency WHERE run_id='{rid}';")=='true')
 reject('durable admission outcome cannot be rewritten',"UPDATE idempotency SET response='{}';")
 box=json.loads(good(f"SELECT payload FROM outbox WHERE run_id='{rid}';"))
 check('outbox payload binds run plan actor and request digest',box=={'run_id':rid,'plan_id':uid(5),'actor_id':uid(2),'request_digest':'a'*64})
 reject('outbox immutable payload cannot be rewritten',"UPDATE outbox SET payload='{}';")
 reject('negative dispatch attempt rejected',"UPDATE outbox SET delivery_attempts=-1;")
 reject('dispatch timestamp requires an attempt',"UPDATE outbox SET dispatched_at=clock_timestamp();")
 good(f"UPDATE outbox SET delivery_attempts=1,dispatched_at=clock_timestamp() WHERE run_id='{rid}';")
 reject('dispatch attempt cannot regress',f"UPDATE outbox SET delivery_attempts=0 WHERE run_id='{rid}';")
 reject('dispatched event cannot lose its timestamp',f"UPDATE outbox SET dispatched_at=NULL WHERE run_id='{rid}';")
 reject('runtime cannot mark outbox delivery',"UPDATE outbox SET delivery_attempts=99;",'42501','fixture_source_worker')
 # Refresh current catalog after schema-006 metadata and private projection are exercised.
 catalog=json.loads(good("SELECT json_agg(json_build_object('table',table_name,'column',column_name,'type',data_type,'nullable',is_nullable) ORDER BY table_name,ordinal_position) FROM information_schema.columns WHERE table_schema='studio_admission';"))
 (root/'docs/quality/physical-schema-catalog.json').write_text(json.dumps({'scope':'Actual PostgreSQL catalog after migrations 001-006 in metadata-chain fixture','columns':catalog,'migration_files':migrations},indent=2)+'\n',encoding='utf-8')

 report['passed']=True
except Exception as ex:report['error']=str(ex)
finally:
 cmd(['docker','rm','--force',container]);report['fixture_removed']=cmd(['docker','inspect',container]).returncode!=0
 report['passed']=report['passed'] and report['fixture_removed'];report['checks']=checks
 (root/'docs/quality/metadata-chain-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
