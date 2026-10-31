"""Disposable isolated service restart regression; never restart the user's stack."""
from pathlib import Path
import copy,datetime,importlib.util,json,secrets,subprocess,time,uuid
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('helpers',Path(__file__).with_name('evaluate-python-runtime-candidates.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
OUT=ROOT/'docs/quality/runtime-candidates/minimal-restart'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 project='mcpstudio-restart-'+uuid.uuid4().hex[:12]
 assert project.startswith('mcpstudio-restart-') and project!='mcpstudio-local'
 folder=(ROOT/'work/runtime-candidates'/project).resolve();assert folder.parent==(ROOT/'work/runtime-candidates').resolve();folder.mkdir()
 secret_values=[secrets.token_urlsafe(32),secrets.token_hex(12),secrets.token_urlsafe(32)]
 def run(args,timeout=240):
  p=subprocess.run([str(a) for a in args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
  if p.returncode:
   message=p.stderr[-3000:]
   for value in secret_values:message=message.replace(value,'[REDACTED]')
   raise RuntimeError(message)
  return p.stdout
 def snapshot(project_name):
  ids=run(['docker','ps','-aq','--filter','label=com.docker.compose.project='+project_name]).split()
  result={}
  for cid in ids:
   obj=json.loads(run(['docker','inspect',cid]))[0]
   result[obj['Config']['Labels']['com.docker.compose.service']]={'id':obj['Id'],'image':obj['Image'],'started_at':obj['State']['StartedAt'],'running':obj['State']['Running'],'ports':obj['HostConfig']['PortBindings']}
  return result
 before=snapshot('mcpstudio-local')
 config=json.loads((ROOT/'.local/services/temporal.yaml').read_text())
 for value in config['persistence']['datastores'].values():value['sql']['password']=secret_values[0]
 (folder/'temporal.json').write_text(json.dumps(config))
 (folder/'s3.json').write_text(json.dumps({'identities':[{'name':'isolated-fixture','credentials':[{'accessKey':secret_values[1],'secretKey':secret_values[2]}],'actions':['Admin','Read','Write','List','Tagging']}]}))
 env=folder/'services.env';env.write_text('MCPSTUDIO_DB_PASSWORD='+secret_values[0]+'\n')
 fixture=folder/'fixture.env';fixture.write_text('LOCAL_S3_ACCESS_KEY='+secret_values[1]+'\nLOCAL_S3_SECRET_KEY='+secret_values[2]+'\nAWS_EC2_METADATA_DISABLED=true\n')
 compose=json.loads((ROOT/'infra/compose.yaml').read_text());compose['name']=project;compose['networks']={'default':{'internal':True}}
 mounts={'./temporal-databases.sql':ROOT/'infra/temporal-databases.sql','./setup-temporal-schema.sh':ROOT/'infra/setup-temporal-schema.sh',
 '../.local/services/temporal.yaml':folder/'temporal.json','./run-temporal.sh':ROOT/'infra/run-temporal.sh','../.local/services/s3.json':folder/'s3.json'}
 for value in compose['services'].values():
  value.pop('ports',None);value['networks']=['default']
  translated=[]
  for v in value['volumes']:
   prefix,target=v.split(':',1)
   translated.append(str(mounts[prefix]).replace('\\','/')+':'+target if prefix in mounts else v)
  value['volumes']=translated
 path=folder/'compose.json';path.write_text(json.dumps(compose))
 base=['docker','compose','--project-name',project,'--file',path,'--env-file',env]
 a=json.loads((ROOT/'docs/quality/runtime-candidates/minimal-runtime/assessment.json').read_text());image=a['image_id']
 report={'complete':False,'passed':False,'project':project,'candidate_image':image,'scope':'Graceful PostgreSQL/Temporal/S3 restart with completed fixture data; not crash recovery or in-flight replay','original_stack_before':before,'checks':[],'cleanup_complete':False}
 def check(name,value):
  report['checks'].append({'name':name,'passed':bool(value)});h.save(OUT/'assessment.json',report)
  assert value,name
 try:
  print('Starting isolated services with unique credentials/volumes and no published ports.',flush=True)
  run(base+['up','-d'],timeout=300)
  initial=snapshot(project);report['isolated_before_restart']=initial
  check('isolated services publish no host ports',all(not v['ports'] for v in initial.values()))
  network=json.loads(run(['docker','network','inspect',project+'_default']))[0]
  check('isolated network is internal',network['Internal'])
  h.container(image,['python','/fixture/service_validation.py'],OUT,project+'_default',fixture)
  print('Restarting only isolated PostgreSQL, Temporal and storage containers.',flush=True)
  run(base+['stop','-t','30','temporal','storage','postgres'])
  run(base+['start','postgres'])
  deadline=time.monotonic()+90
  while time.monotonic()<deadline:
   cid=run(base+['ps','-q','postgres']).strip()
   if cid and json.loads(run(['docker','inspect',cid]))[0]['State'].get('Health',{}).get('Status')=='healthy':break
   time.sleep(2)
  else:raise RuntimeError('Isolated PostgreSQL restart health deadline')
  run(base+['start','temporal','storage'])
  after=snapshot(project);report['isolated_after_restart']=after
  check('all three isolated data services actually restarted',all(after[n]['id']==initial[n]['id'] and after[n]['started_at']!=initial[n]['started_at'] for n in ['postgres','temporal','storage']))
  fixture.write_text(fixture.read_text()+'FIXTURE_PHASE=restart\n')
  h.container(image,['python','/fixture/service_validation.py'],OUT,project+'_default',fixture)
  result=json.loads((OUT/'local-service-validation.json').read_text())
  check('fixture workflow and object persist across isolated service restarts',result['passed'] and result['restart_phase_complete'])
  check('unique fixture object removed',result['fixture_object_removed'])
  report['service_checks']=len(result['checks']);report['complete']=True
 finally:
  # Never issue a broad prune. Compose resource names are uniquely generated and
  # every discovered container must carry this invocation's exact project label.
  for cid in run(['docker','ps','-aq','--filter','label=com.docker.compose.project='+project]).split():
   labels=json.loads(run(['docker','inspect',cid]))[0]['Config']['Labels'];assert labels['com.docker.compose.project']==project
  run(base+['down','--volumes','--timeout','30'],timeout=180)
  remaining={kind:run(['docker',kind,'ls','-q','--filter','label=com.docker.compose.project='+project]).strip() for kind in ['container','volume','network']}
  report['cleanup_complete']=not any(remaining.values());check('isolated containers volumes and network removed',report['cleanup_complete'])
  report['original_stack_after']=snapshot('mcpstudio-local');check('original stack IDs and startup times unchanged',report['original_stack_after']==before)
  for name in ['services.env','fixture.env','temporal.json','s3.json']:
   target=(folder/name).resolve();assert target.parent==folder;target.unlink(missing_ok=True)
  report['ephemeral_credentials_removed']=True
  report['passed']=report['complete'] and all(c['passed'] for c in report['checks'])
  h.save(OUT/'assessment.json',report)
 print('Isolated restart checks passed; temporary services/data removed; original stack unchanged.',flush=True)
if __name__=='__main__':main()
