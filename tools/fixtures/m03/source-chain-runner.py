"""Ownership-chain regression and real-login smoke test across migrations 001-004."""
from pathlib import Path
import concurrent.futures,hashlib,json,secrets,subprocess,sys,time,uuid
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'work/python-tools'))
import rfc8785
image=json.loads((root/'docs/quality/local-service-images.json').read_text())['images']['postgres']
container='mcpstudio-source-'+uuid.uuid4().hex[:12];checks=[]
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
report={'scope':'Source snapshot/graph/recommendation physical ownership plus migration 001-004 role integration; trusted source evidence fixtures only','image':image,'published_ports':False,'passed':False}
try:
 p=cmd(['docker','run','-d','--rm','--name',container,'--network','none','--memory','512m','--cpus','1','--tmpfs','/var/lib/postgresql/data:rw,size=512m','-e','POSTGRES_PASSWORD='+secrets.token_urlsafe(32),image])
 if p.returncode:raise RuntimeError(p.stderr)
 for _ in range(40):
  if cmd(['docker','exec',container,'pg_isready','-U','postgres']).returncode==0:break
  time.sleep(.5)
 migrations=['001_admission_kernel.sql','002_bound_validation.sql','003_runtime_roles.sql','004_source_graph_recommendation.sql']
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
 good(f"INSERT INTO approval VALUES({T},{AP},{PL},{A},'{hashlib.sha256(payload()).hexdigest()}',NULL);CREATE ROLE fixture_source_backend LOGIN IN ROLE studio_backend;CREATE ROLE fixture_source_worker LOGIN IN ROLE studio_worker;INSERT INTO runtime_principal VALUES('fixture_source_backend',{T},{A},'backend',true),('fixture_source_worker',{T},{A},'worker',true);")
 rid=good(f"SELECT backend_submit({PL},{AP},'source-chain',repeat('a',64));",'fixture_source_backend');check('scoped backend admits fully linked plan',bool(rid))
 good(f"INSERT INTO worker_assignment VALUES('fixture_source_worker',{T},'{rid}',true);")
 good(f"SELECT worker_publish('{rid}',repeat('e',64));",'fixture_source_worker')
 vid=good(f"SELECT backend_validate('{rid}');",'fixture_source_backend')
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
 (root/'docs/quality/physical-schema-catalog.json').write_text(json.dumps({'scope':'Actual PostgreSQL catalog after migrations 001-004 in source-chain fixture','columns':catalog,'migration_files':migrations},indent=2)+'\n',encoding='utf-8')
 report['passed']=True
except Exception as ex:report['error']=str(ex)
finally:
 cmd(['docker','rm','--force',container]);report['fixture_removed']=cmd(['docker','inspect',container]).returncode!=0
 report['passed']=report['passed'] and report['fixture_removed'];report['checks']=checks
 (root/'docs/quality/source-chain-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
