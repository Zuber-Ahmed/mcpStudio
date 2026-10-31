"""Apply and test the partial admission migration in an isolated disposable PostgreSQL."""
from pathlib import Path
import concurrent.futures,json,secrets,subprocess,time,uuid
root=Path(__file__).resolve().parents[3]
image=json.loads((root/'docs/quality/local-service-images.json').read_text())['images']['postgres']
container='mcpstudio-admission-'+uuid.uuid4().hex[:12]
checks=[]
def command(args,**kwargs):return subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=60,**kwargs)
def sql(text):return command(['docker','exec','-i',container,'psql','-U','postgres','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose'],input='SET search_path=studio_admission,pg_catalog;\n'+text)
def ok(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise RuntimeError(name)
def good(text):
 p=sql(text)
 if p.returncode:raise RuntimeError(p.stderr)
 return p.stdout.strip()
def reject(name,text,code='23514'):
 p=sql(text);ok(name,p.returncode!=0 and code in p.stderr)
def id(n):return "'00000000-0000-4000-8000-%012d'"%n
T,A,P,AN,PL,AP,C=[id(n) for n in range(1,8)]
digest="repeat('a',64)::digest"
def admit(key='one',d=digest,consent='NULL',provider='NULL',classes='NULL',redaction='NULL',retention='NULL',plan=PL,approval=AP,actor=A):
 return f"SELECT admit({T},{actor},{plan},{approval},'{key}',{d},{consent},{provider},{classes},{redaction},{retention});"
def scoped(key='scope',**changes):
 args=dict(key=key,consent=C,provider="'local-provider'",classes="ARRAY['signatures']",redaction="'redact-v1'",retention="'local fixture retention'");args.update(changes);return admit(**args)
report={'scope':'Implemented partial foundation admission kernel, migration and independent-session transaction tests; no API, inference execution or full 23-entity schema','image':image,'published_ports':False,'passed':False}
try:
 p=command(['docker','run','-d','--rm','--name',container,'--network','none','--memory','512m','--cpus','1','--tmpfs','/var/lib/postgresql/data:rw,size=512m','-e','POSTGRES_PASSWORD='+secrets.token_urlsafe(32),image])
 if p.returncode:raise RuntimeError(p.stderr)
 for _ in range(40):
  if command(['docker','exec',container,'pg_isready','-U','postgres']).returncode==0:break
  time.sleep(.5)
 migration=root/'infra/database/migrations/001_admission_kernel.sql'
 good(migration.read_text());ok('migration applies atomically on empty PostgreSQL',True)
 good(f"""INSERT INTO tenant VALUES({T}),({id(20)});
 INSERT INTO actor VALUES({A}),({id(21)});
 INSERT INTO membership VALUES({T},{A},true);
 INSERT INTO project VALUES({T},{P}),({T},{id(22)}),({id(20)},{id(23)});
 INSERT INTO analysis(tenant_id,project_id,id,source_digest) VALUES({T},{P},{AN},{digest});
 SELECT new_plan({T},{AN},{PL},{digest});
 INSERT INTO approval VALUES({T},{AP},{PL},{A},{digest},NULL);
 INSERT INTO consent VALUES({T},{C},{P},{A},{digest},'local-provider',ARRAY['signatures'],'redact-v1','local fixture retention',now()+interval '1 hour',NULL);""")
 first=good(admit());ok('current scoped approval admits local run',bool(first))
 ok('same key and same body returns original run',good(admit())==first)
 reject('changed digest conflicts with existing key',admit(d="repeat('b',64)::digest"),'P0409')
 reject('same digest but changed body conflicts',scoped(key='one'),'P0409')
 reject('foreign actor denied',admit(key='foreign',actor=id(21)))
 reject('inference without consent denied',admit(key='noconsent',provider="'local-provider'"))
 ok('matching explicit consent accepted',bool(good(scoped())))
 for name,changes in [('wrong provider',{'provider':"'other'"}),('extra payload class',{'classes':"ARRAY['source']"}),('null payload class',{'classes':'ARRAY[NULL]::text[]'}),('empty payload class',{'classes':'ARRAY[]::text[]'}),('changed redaction',{'redaction':"'other'"}),('changed retention',{'retention':"'other'"})]:
  reject(name+' denied',scoped(key=name,**changes))
 for name,update,restore in [
 ('expired consent',"expires_at=now()-interval '1 second'","expires_at=now()+interval '1 hour'"),
 ('revoked consent','revoked_at=now()','revoked_at=NULL'),
 ('changed source consent',"source_digest=repeat('b',64)","source_digest=repeat('a',64)"),
 ('foreign project consent',f'project_id={id(22)}',f'project_id={P}'),
 ('foreign actor consent',f'actor_id={id(21)}',f'actor_id={A}')]:
  good(f'UPDATE consent SET {update} WHERE id={C};');reject(name+' denied',scoped(key=name));good(f'UPDATE consent SET {restore} WHERE id={C};')
 reject('cross tenant analysis parent denied',f"INSERT INTO analysis(tenant_id,project_id,id,source_digest) VALUES({id(20)},{P},{id(24)},{digest});",'23503')
 reject('terminal run without completion time denied',"UPDATE run SET status='succeeded';")
 reject('referenced approval deletion restricted',f'DELETE FROM approval WHERE id={AP};','23503')
 # The pair uses separate psql sessions; server row locks serialize admission.
 with concurrent.futures.ThreadPoolExecutor(2) as pool:
  result=list(pool.map(lambda _:good(admit(key='concurrent')),range(2)))
 ok('concurrent identical requests return one resource',len(set(result))==1)
 ok('concurrent admission creates one outbox identity',good("SELECT count(*) FROM outbox WHERE run_id=(SELECT run_id FROM idempotency WHERE key='concurrent');")=='1')
 before=good('SELECT count(*) FROM run;')
 outbox_before=good('SELECT count(*) FROM outbox;')
 reject('failed admission rolls back run and outbox',scoped(key='rollback',provider="'wrong'"))
 ok('rejected admission has no persisted run',good('SELECT count(*) FROM run;')==before and good('SELECT count(*) FROM outbox;')==outbox_before)
 # Prove admission waits behind a revocation already in flight, then rejects it.
 for kind,update,restore,call in [
 ('approval',f'UPDATE approval SET revoked_at=now() WHERE id={AP};',f'UPDATE approval SET revoked_at=NULL WHERE id={AP};',admit(key='approval-race')),
 ('membership',f'UPDATE membership SET active=false WHERE actor_id={A};',f'UPDATE membership SET active=true WHERE actor_id={A};',admit(key='rights-race')),
 ('consent',f'UPDATE consent SET revoked_at=now() WHERE id={C};',f'UPDATE consent SET revoked_at=NULL WHERE id={C};',scoped(key='consent-race'))]:
  with concurrent.futures.ThreadPoolExecutor(2) as pool:
   future=pool.submit(good,f"SET application_name='revoke-{kind}'; BEGIN; {update} SELECT pg_sleep(3); COMMIT;")
   observed=False
   for _ in range(50):
    if good(f"SELECT count(*) FROM pg_stat_activity WHERE application_name='revoke-{kind}' AND wait_event='PgSleep';")=='1':observed=True;break
    time.sleep(.03)
   ok(kind+' revocation lock observed in independent session',observed)
   blocked=pool.submit(sql,call)
   waiting=False
   for _ in range(35):
    if good("SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid))>0;")!='0':waiting=True;break
    time.sleep(.03)
   ok(kind+' admission waits for revocation transaction',waiting)
   future.result();response=blocked.result()
   ok(kind+' concurrent committed revocation denies admission',response.returncode!=0 and '23514' in response.stderr)
  good(restore)
 # Monotonic versions are allocated under the parent row lock, across sessions.
 with concurrent.futures.ThreadPoolExecutor(2) as pool:
  versions=list(pool.map(lambda n:good(f'SELECT new_plan({T},{AN},{id(n)},{digest});'),[30,31]))
 ok('concurrent plan versions are monotonic and unique',set(versions)=={'2','3'})
 ok('one current plan after concurrent publication',good('SELECT count(*) FROM plan WHERE current;')=='1')
 reject('superseded plan cannot replay prior admission',admit())
 # Explicit transaction rollback must remove all admitted effects.
 latest=good('SELECT id FROM plan WHERE current;')
 good(f"INSERT INTO approval VALUES({T},{id(32)},'{latest}',{A},{digest},NULL);")
 good('BEGIN;'+admit(key='abort',plan="'"+latest+"'",approval=id(32))+'ROLLBACK;')
 ok('transaction rollback removes idempotency and outbox effects',good("SELECT count(*) FROM idempotency WHERE key='abort';")=='0' and good('SELECT count(*) FROM run;')==before and good('SELECT count(*) FROM outbox;')==outbox_before)
 report['passed']=True
except Exception as ex:report['error']=str(ex)
finally:
 command(['docker','rm','--force',container])
 report['fixture_removed']=command(['docker','inspect',container]).returncode!=0
 report['checks']=checks;report['passed']=report['passed'] and report['fixture_removed']
 (root/'docs/quality/admission-transaction-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
