"""Real login sessions test the private kernel and scoped definer interfaces."""
from pathlib import Path
import hashlib,json,secrets,subprocess,sys,time,uuid
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'work/python-tools'))
import rfc8785
image=json.loads((root/'docs/quality/local-service-images.json').read_text())['images']['postgres']
container='mcpstudio-roles-'+uuid.uuid4().hex[:12];checks=[]
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
def denied(n,s,user,state='42501'):
 p=sql(s,user);check(n,p.returncode!=0 and state in p.stderr)
def uid(n):return '00000000-0000-4000-8000-%012d'%n
def U(n):return "'"+uid(n)+"'"
T,A,P,AN,PL,AP,PO,CA=map(U,range(1,9))
report={'scope':'Real PostgreSQL login-session privileges and scoped definer wrapper integration across migrations 001-003; no production principal provisioning or HTTP authentication','image':image,'passed':False,'published_ports':False}
try:
 p=cmd(['docker','run','-d','--rm','--name',container,'--network','none','--memory','512m','--cpus','1','--tmpfs','/var/lib/postgresql/data:rw,size=512m','-e','POSTGRES_PASSWORD='+secrets.token_urlsafe(32),image])
 if p.returncode:raise RuntimeError(p.stderr)
 for _ in range(40):
  if cmd(['docker','exec',container,'pg_isready','-U','postgres']).returncode==0:break
  time.sleep(.5)
 for filename in ['001_admission_kernel.sql','002_bound_validation.sql','003_runtime_roles.sql']:
  good((root/'infra/database/migrations'/filename).read_text());check(filename+' applies',True)
 good(f"""INSERT INTO tenant VALUES({T}),({U(20)}); INSERT INTO actor VALUES({A}),({U(21)});
 INSERT INTO membership VALUES({T},{A},true),({U(20)},{U(21)},true);
 INSERT INTO project VALUES({T},{P});
 INSERT INTO analysis(tenant_id,project_id,id,source_digest) VALUES({T},{P},{AN},repeat('a',64));
 INSERT INTO validation_policy VALUES({T},{PO},1,ARRAY['compile']);
 INSERT INTO candidate VALUES({T},{AN},{CA},true,'fixture.ts:1');
 CREATE ROLE fixture_backend LOGIN IN ROLE studio_backend;
 CREATE ROLE fixture_foreign LOGIN IN ROLE studio_backend;
 CREATE ROLE fixture_unmapped LOGIN IN ROLE studio_backend;
 CREATE ROLE fixture_worker LOGIN IN ROLE studio_worker;
 CREATE ROLE fixture_unassigned LOGIN IN ROLE studio_worker;
 CREATE ROLE fixture_plain LOGIN;
 INSERT INTO runtime_principal VALUES('fixture_backend',{T},{A},'backend',true),
 ('fixture_foreign',{U(20)},{U(21)},'backend',true),('fixture_worker',{T},{A},'worker',true),('fixture_unassigned',{T},{A},'worker',true);""")
 body=rfc8785.dumps(dict(analysis_id=uid(4),source_digest='a'*64,policy_id=uid(7),policy_version=1,candidate_ids=[uid(8)],mode='server',transport='stdio'))
 h=hashlib.sha256(body).hexdigest()
 good(f"SELECT new_plan({T},{AN},{PL},'{h}');INSERT INTO plan_binding VALUES({T},{PL},{PO},1,decode('{body.hex()}','hex'),repeat('a',64));INSERT INTO approval VALUES({T},{AP},{PL},{A},'{h}',NULL);")
 for user in ['fixture_backend','fixture_worker','fixture_plain']:
  for name,statement in [('raw read','SELECT * FROM studio_admission.run;'),('raw write',"UPDATE studio_admission.run SET status='running';"),('audit insertion',f"INSERT INTO studio_admission.audit_event(tenant_id,entity,entity_key,event_type) VALUES({T},'forged','{{}}','INSERT');"),('audit truncation','TRUNCATE studio_admission.audit_event;'),('DDL','CREATE TABLE studio_admission.escape(id integer);'),('internal function',f"SELECT studio_admission.new_plan({T},{AN},{U(90)},repeat('b',64)::studio_admission.digest);"),('owner role switch','SET ROLE studio_kernel_owner;')]:
   denied(user+' '+name+' denied',statement,user)
 denied('unmapped backend cannot claim identity',f"SELECT backend_submit({PL},{AP},'missing',repeat('a',64));",'fixture_unmapped')
 denied('plain login cannot invoke public backend wrapper',f"SELECT studio_admission.backend_submit({PL},{AP},'plain',repeat('a',64));",'fixture_plain')
 denied('backend cannot execute worker publication',f"SELECT worker_publish({U(90)},repeat('a',64));",'fixture_backend')
 denied('worker cannot execute backend admission',f"SELECT backend_submit({PL},{AP},'wrong-role',repeat('a',64));",'fixture_worker')
 denied('runtime cannot set session authorization to owner','SET SESSION AUTHORIZATION studio_kernel_owner;','fixture_backend')
 # Search-path and custom-setting spoofing cannot change authenticated identity.
 denied('custom tenant settings cannot spoof identity',f"SET studio.tenant_id={T};SET studio.actor_id={A};SELECT backend_submit({PL},{AP},'spoof',repeat('a',64));",'fixture_foreign','23503')
 rid=good(f"SELECT backend_submit({PL},{AP},'one',repeat('a',64));",'fixture_backend')
 check('mapped backend admits its own run',bool(rid))
 check('backend sees own run status',good(f"SELECT backend_run_status('{rid}');",'fixture_backend')=='queued')
 denied('foreign tenant run status denied',f"SELECT backend_run_status('{rid}');",'fixture_foreign')
 check('authorized replay returns same run',good(f"SELECT backend_submit({PL},{AP},'one',repeat('a',64));",'fixture_backend')==rid)
 denied('unassigned worker cannot publish run',f"SELECT worker_publish('{rid}',repeat('e',64));",'fixture_unassigned')
 denied('worker cannot assign itself',f"INSERT INTO worker_assignment VALUES('fixture_worker',{T},'{rid}',true);",'fixture_worker')
 good(f"INSERT INTO worker_assignment VALUES('fixture_worker',{T},'{rid}',true);")
 # Deliberately shadow private table names in the caller's temporary schema.
 output=good(f"CREATE TEMP TABLE membership(tenant_id uuid,actor_id uuid,active boolean);CREATE TEMP TABLE run(id uuid,status text);SET search_path=pg_temp,public;SELECT studio_admission.backend_run_status('{rid}');",'fixture_backend')
 check('temporary shadow tables cannot redirect definer lookup',output=='queued')
 good(f"SELECT worker_publish('{rid}',repeat('e',64));",'fixture_worker');check('assigned worker publishes through guarded function',True)
 denied('worker cannot republish terminal generation',f"SELECT worker_publish('{rid}',repeat('f',64));",'fixture_worker','23514')
 vid=good(f"SELECT backend_validate('{rid}');",'fixture_backend');check('backend queues bound validation',bool(vid))
 denied('foreign tenant cannot queue validation',f"SELECT backend_validate('{rid}');",'fixture_foreign')
 evidence=f"SELECT worker_check('{vid}','compile','passed','fixture-check','fixture-v1',0,now(),now(),'fixture-log',NULL);"
 denied('unassigned worker cannot record evidence',evidence,'fixture_unassigned')
 good(evidence,'fixture_worker');check('assigned worker records mandatory execution evidence',True)
 good(f"SELECT worker_finish_validation('{vid}');",'fixture_worker')
 denied('finalized evidence cannot be overwritten through wrapper',evidence,'fixture_worker','23514')
 exported=good(f"SELECT backend_export('{vid}');",'fixture_backend');check('authorized backend completes gated export',bool(exported))
 denied('foreign tenant cannot export',f"SELECT backend_export('{vid}');",'fixture_foreign','23514')
 good("UPDATE runtime_principal SET enabled=false WHERE login_name='fixture_backend';")
 denied('disabled principal loses wrapper access',f"SELECT backend_run_status('{rid}');",'fixture_backend')
 good("UPDATE runtime_principal SET enabled=true WHERE login_name='fixture_backend';UPDATE membership SET active=false WHERE tenant_id="+T+';')
 denied('removed membership loses wrapper access',f"SELECT backend_run_status('{rid}');",'fixture_backend')
 good('UPDATE membership SET active=true WHERE tenant_id='+T+";UPDATE worker_assignment SET enabled=false;")
 denied('revoked assignment loses worker access',f"SELECT worker_finish_validation('{vid}');",'fixture_worker')
 denied('worker cannot enable its assignment','UPDATE worker_assignment SET enabled=true;','fixture_worker')
 check('runtime roles have no elevated flags',good("SELECT count(*) FROM pg_roles WHERE rolname IN ('studio_kernel_owner','studio_backend','studio_worker') AND (rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls OR rolcanlogin);")=='0')
 check('definer functions owned by non-login kernel role',good("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='studio_admission' AND p.prosecdef AND p.proowner <> 'studio_kernel_owner'::regrole;")=='0')
 check('all kernel functions have hardened search path',good("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='studio_admission' AND NOT coalesce(p.proconfig @> ARRAY['search_path=pg_catalog, studio_admission, pg_temp'],false);")=='0')
 # Future functions created by the designated owner must not inherit PUBLIC execute.
 good("SET ROLE studio_kernel_owner;CREATE FUNCTION studio_admission.future_private() RETURNS integer LANGUAGE sql AS 'SELECT 1';RESET ROLE;")
 denied('future owner function is private by default','SELECT future_private();','fixture_backend')
 check('successful export audit exists without runtime audit grants',good("SELECT count(*) FROM audit_event WHERE entity='export_record';")=='1')
 catalog=json.loads(good("SELECT json_agg(json_build_object('table',table_name,'column',column_name,'type',data_type,'nullable',is_nullable) ORDER BY table_name,ordinal_position) FROM information_schema.columns WHERE table_schema='studio_admission';"))
 check('physical catalog includes runtime principal and assignment boundaries',{'runtime_principal','worker_assignment'}.issubset({c['table'] for c in catalog}))
 (root/'docs/quality/physical-schema-catalog.json').write_text(json.dumps({'scope':'Actual PostgreSQL catalog after migrations 001-003 in the role fixture','columns':catalog,'migration_files':['001_admission_kernel.sql','002_bound_validation.sql','003_runtime_roles.sql']},indent=2)+'\n')
 report['passed']=True
except Exception as ex:report['error']=str(ex)
finally:
 cmd(['docker','rm','--force',container]);report['fixture_removed']=cmd(['docker','inspect',container]).returncode!=0
 report['passed']=report['passed'] and report['fixture_removed'];report['checks']=checks
 (root/'docs/quality/runtime-role-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
