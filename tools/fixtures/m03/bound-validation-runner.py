"""Exercise migrations 001+002 together; no application database is changed."""
from pathlib import Path
import concurrent.futures,hashlib,json,secrets,subprocess,sys,time,uuid
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'work/python-tools'))
import rfc8785
image=json.loads((root/'docs/quality/local-service-images.json').read_text())['images']['postgres']
container='mcpstudio-binding-'+uuid.uuid4().hex[:12]
checks=[]
def cmd(args,**kw):return subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=60,**kw)
def sql(s):return cmd(['docker','exec','-i',container,'psql','-U','postgres','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose'],input='SET search_path=studio_admission,pg_catalog;\n'+s)
def check(n,ok):
 checks.append({'name':n,'passed':bool(ok)})
 if not ok:raise RuntimeError(n)
def good(s):
 p=sql(s)
 if p.returncode:raise RuntimeError(p.stderr)
 return p.stdout.strip()
def reject(n,s,state='23514'):
 p=sql(s);check(n,p.returncode!=0 and state in p.stderr)
def uid(n):return '00000000-0000-4000-8000-%012d'%n
def U(n):return "'"+uid(n)+"'"
T,A,P,AN,PL,AP,PO,CA=map(U,range(1,9))
def lit(s):return "'"+s.replace("'","''")+"'"
def payload(**changes):
 p=dict(analysis_id=uid(4),source_digest='a'*64,policy_id=uid(7),policy_version=1,candidate_ids=[uid(8)],mode='server',transport='stdio')
 p.update(changes);return rfc8785.dumps(p)
def create_plan(n,body):
 sha=hashlib.sha256(body).hexdigest()
 return f"SELECT new_plan({T},{AN},{U(n)},'{sha}');"
def bind(n,body,policy=PO,source="repeat('a',64)"):
 return f"INSERT INTO plan_binding VALUES({T},{U(n)},{policy},1,decode('{body.hex()}','hex'),{source});"
def export(v=20,d="repeat('e',64)",actor=A,n=40):
 return f"INSERT INTO export_record(tenant_id,id,validation_id,actor_id,artifact_digest,classification) VALUES({T},{U(n)},{U(v)},{actor},{d},'APPROVED');"
def record(name,status='passed',exit_code=0,reason='NULL'):
 return f"UPDATE validation_check SET status='{status}',command='fixture-check',tool_version='fixture-v1',exit_code={exit_code},started_at=now(),completed_at=now(),log_reference='fixture-log',reason={reason} WHERE validation_id={U(20)} AND name='{name}';"
report={'scope':'Physical plan/policy binding, validation/export guard and append-only audit slice; trusted evidence fixtures, not object-byte verification or application API','image':image,'passed':False,'published_ports':False}
try:
 p=cmd(['docker','run','-d','--rm','--name',container,'--network','none','--memory','512m','--cpus','1','--tmpfs','/var/lib/postgresql/data:rw,size=512m','-e','POSTGRES_PASSWORD='+secrets.token_urlsafe(32),image])
 if p.returncode:raise RuntimeError(p.stderr)
 for _ in range(40):
  if cmd(['docker','exec',container,'pg_isready','-U','postgres']).returncode==0:break
  time.sleep(.5)
 for name in ['001_admission_kernel.sql','002_bound_validation.sql']:
  good((root/'infra/database/migrations'/name).read_text());check('migration '+name+' applies',True)
 good(f"""INSERT INTO tenant VALUES({T}),({U(50)}); INSERT INTO actor VALUES({A}),({U(51)});
 INSERT INTO membership VALUES({T},{A},true); INSERT INTO project VALUES({T},{P});
 INSERT INTO analysis(tenant_id,project_id,id,source_digest) VALUES({T},{P},{AN},repeat('a',64)),({T},{P},{U(52)},repeat('b',64));
 INSERT INTO validation_policy VALUES({T},{PO},1,ARRAY['compile','auth']),({T},{U(53)},1,ARRAY['compile']);
 INSERT INTO candidate VALUES({T},{AN},{CA},true,'fixture.ts:1'),({T},{AN},{U(54)},false,'fixture.ts:2'),({T},{U(52)},{U(55)},true,'other.ts:1');""")
 reject('empty mandatory policy denied',f"INSERT INTO validation_policy VALUES({T},{U(60)},1,ARRAY[]::text[]);")
 reject('duplicate mandatory check denied',f"INSERT INTO validation_policy VALUES({T},{U(60)},1,ARRAY['compile','compile']);")
 reject('null mandatory check denied',f"INSERT INTO validation_policy VALUES({T},{U(60)},1,ARRAY[NULL]::text[]);")
 reject('blank mandatory check denied',f"INSERT INTO validation_policy VALUES({T},{U(60)},1,ARRAY[' ']);")
 for name,changes in [('foreign analysis',{'analysis_id':uid(52)}),('changed source',{'source_digest':'b'*64}),('wrong policy',{'policy_id':uid(53)}),('wrong policy version',{'policy_version':2}),('duplicate candidates',{'candidate_ids':[uid(8),uid(8)]}),('foreign candidate',{'candidate_ids':[uid(55)]}),('ineligible candidate',{'candidate_ids':[uid(54)]}),('empty candidates',{'candidate_ids':[]}),('unsupported mode',{'mode':'client'}),('unsupported transport',{'transport':'http'})]:
  b=payload(**changes);reject(name+' denied','BEGIN;'+create_plan(61,b)+bind(61,b))
 b=payload();reject('changed bytes do not match plan digest','BEGIN;'+create_plan(61,b)+bind(61,b+b' '))
 good(create_plan(5,b)+bind(5,b));check('canonical payload hash and binding accepted',True)
 check('candidate links derive from exact bound payload',good('SELECT count(*) FROM plan_candidate;')=='1')
 reject('unbound extra candidate link denied',f'INSERT INTO plan_candidate VALUES({T},{PL},{AN},{U(54)});')
 for name,s in [('policy mutation',f"UPDATE validation_policy SET required_checks=ARRAY['compile'];"),('plan hash mutation',f"UPDATE plan SET plan_hash=repeat('b',64);"),('binding mutation',"UPDATE plan_binding SET canonical_payload=decode('00','hex');"),('candidate mutation',"UPDATE candidate SET eligible=true;"),('analysis source mutation',"UPDATE analysis SET source_digest=repeat('c',64);")]:reject(name+' denied',s)
 good(f"INSERT INTO approval VALUES({T},{AP},{PL},{A},'{hashlib.sha256(b).hexdigest()}',NULL);")
 rid=good(f"SELECT admit({T},{A},{PL},{AP},'bound',repeat('a',64)::digest);")
 report['fixture_run_id']=rid
 reject('admission without bound plan denied','BEGIN;'+create_plan(62,b)+f"INSERT INTO approval VALUES({T},{U(63)},{U(62)},{A},'{hashlib.sha256(b).hexdigest()}',NULL); SELECT admit({T},{A},{U(62)},{U(63)},'unbound',repeat('a',64)::digest);")
 reject('run cannot change admitted identity',f"UPDATE run SET request_digest=repeat('b',64);")
 good(f"INSERT INTO artifact_set VALUES({T},'{rid}',repeat('e',64));")
 reject('validation requires succeeded generation',f"INSERT INTO validation(tenant_id,id,run_id,artifact_digest,policy_id,policy_version) VALUES({T},{U(20)},'{rid}',repeat('e',64),{PO},1);")
 good("UPDATE run SET status='succeeded',completed_at=now();")
 reject('terminal generation cannot be reopened',"UPDATE run SET status='running',completed_at=NULL;")
 reject('artifact digest replacement denied',"UPDATE artifact_set SET artifact_digest=repeat('f',64);")
 reject('changed artifact validation denied',f"INSERT INTO validation(tenant_id,id,run_id,artifact_digest,policy_id,policy_version) VALUES({T},{U(20)},'{rid}',repeat('f',64),{PO},1);",'23503')
 reject('weaker policy validation denied',f"INSERT INTO validation(tenant_id,id,run_id,artifact_digest,policy_id,policy_version) VALUES({T},{U(20)},'{rid}',repeat('e',64),{U(53)},1);")
 good(f"INSERT INTO validation(tenant_id,id,run_id,artifact_digest,policy_id,policy_version) VALUES({T},{U(20)},'{rid}',repeat('e',64),{PO},1);")
 check('all mandatory checks initialized not_run',good("SELECT count(*) FROM validation_check WHERE status='not_run';")=='2')
 reject('queued validation cannot export',export())
 reject('passed requires execution metadata',"UPDATE validation_check SET status='passed',reason=NULL;")
 reject('nonzero exit cannot pass',record('compile',exit_code=1))
 reject('failed exit zero requires assertion reason',record('compile',status='failed',exit_code=0))
 reject('skipped cannot carry execution evidence',record('compile',status='skipped',reason="'unavailable'"))
 reject('check identity cannot be moved',f"UPDATE validation_check SET name='other' WHERE name='compile';")
 reject('mandatory check cannot be deleted',"DELETE FROM validation_check WHERE name='compile';")
 reject('skipped mandatory check blocks completed export',
  "BEGIN;UPDATE validation_check SET status='skipped',reason='fixture unavailable' WHERE name='auth';"+
  record('compile')+"UPDATE validation SET status='completed',completed_at=now();"+export())
 reject('failed assertion with exit zero blocks export',
  'BEGIN;'+record('compile')+record('auth',status='failed',exit_code=0,reason="'identity assertion failed'")+
  "UPDATE validation SET status='completed',completed_at=now();"+export())
 reject('failed validation cannot export despite passing checks',
  'BEGIN;'+record('compile')+record('auth')+"UPDATE validation SET status='failed',completed_at=now();"+export())
 good(record('compile')+"UPDATE validation SET status='completed',completed_at=now();")
 reject('completed validation with missing pass cannot export',export())
 reject('finalized check cannot be forged later',record('auth'))
 # Create a second normal execution for the successful gate; the first remains truthful.
 good(f"INSERT INTO validation(tenant_id,id,run_id,artifact_digest,policy_id,policy_version) VALUES({T},{U(21)},'{rid}',repeat('e',64),{PO},1);")
 good((record('compile')+record('auth')).replace(U(20),U(21))+f"UPDATE validation SET status='completed',completed_at=now() WHERE id={U(21)};")
 reject('export binds exact artifact digest',export(v=21,d="repeat('f',64)"))
 reject('foreign actor cannot export',export(v=21,actor=U(51)))
 reject('revoked approval denies export','BEGIN;'+f'UPDATE approval SET revoked_at=now() WHERE id={AP};'+export(v=21))
 reject('superseded plan denies export','BEGIN;'+create_plan(64,b)+export(v=21))
 good(export(v=21));check('all required evidence permits approved record',True)
 reject('audit cannot update',"UPDATE audit_event SET event_type='forged';")
 reject('audit cannot delete','DELETE FROM audit_event;')
 reject('audit cannot truncate','TRUNCATE audit_event;')
 reject('export record cannot be relabeled',"UPDATE export_record SET classification='APPROVED';")
 check('successful export has atomic audit entry',good("SELECT count(*) FROM audit_event WHERE entity='export_record';")=='1')
 count=good('SELECT count(*) FROM audit_event;')
 good('BEGIN;'+export(v=21,n=41)+'ROLLBACK;')
 check('export rollback also removes audit event',good('SELECT count(*) FROM audit_event;')==count)
 # A final independent-session race proves export waits behind approval revocation.
 with concurrent.futures.ThreadPoolExecutor(2) as pool:
  future=pool.submit(good,f"SET application_name='export-revoke';BEGIN;UPDATE approval SET revoked_at=now() WHERE id={AP};SELECT pg_sleep(3);COMMIT;")
  seen=False
  for _ in range(60):
   if good("SELECT count(*) FROM pg_stat_activity WHERE application_name='export-revoke' AND wait_event='PgSleep';")=='1':seen=True;break
   time.sleep(.02)
  check('export revocation transaction lock observed',seen)
  attempt=pool.submit(sql,export(v=21,n=42));blocked=False
  for _ in range(40):
   if good('SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid))>0;')!='0':blocked=True;break
   time.sleep(.02)
  check('export waits for revocation transaction',blocked)
  future.result();p=attempt.result();check('committed concurrent revocation denies export',p.returncode!=0 and '23514' in p.stderr)
 report['passed']=True
except Exception as ex:report['error']=str(ex)
finally:
 cmd(['docker','rm','--force',container]);report['fixture_removed']=cmd(['docker','inspect',container]).returncode!=0
 report['passed']=report['passed'] and report['fixture_removed'];report['checks']=checks
 (root/'docs/quality/bound-validation-results.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
