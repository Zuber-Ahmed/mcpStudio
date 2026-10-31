"""Evaluate isolated pip-free candidates; never update adopted tags or restart services."""
from pathlib import Path
import collections, datetime, hashlib, json, subprocess, uuid, sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/quality/runtime-candidates/python-tooling-free'
WORK = ROOT / 'work/runtime-candidates/python-tooling-free'

def run(args, timeout=240):
    p = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if p.returncode:
        raise RuntimeError(f'Command failed ({p.returncode}): {p.stderr[-2000:]}')
    return p.stdout

def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')

def inspect(ref):
    return json.loads(run(['docker', 'image', 'inspect', ref]))[0]

def container(image, args, evidence=None, network='none', envfile=None):
    name = 'mcpstudio-candidate-'+uuid.uuid4().hex
    cmd = ['docker','run','--rm','--name',name,'--network',network,'--read-only',
           '--cap-drop','ALL','--security-opt','no-new-privileges','--user','65534:65534',
           '--memory','512m','--cpus','1','--pids-limit','64','--tmpfs','/tmp:rw,noexec,nosuid,size=32m']
    if evidence: cmd += ['--mount',f'type=bind,source={evidence},target=/evidence']
    if envfile: cmd += ['--env-file',envfile]
    try: return run(cmd+[image]+args, timeout=160)
    finally:
        subprocess.run(['docker','rm','-f',name], capture_output=True)

PRUNE = '''import pathlib,shutil
base=pathlib.Path('/usr/local/lib/python3.14')
targets=[base/'ensurepip',base/'site-packages/pip',*list((base/'site-packages').glob('pip-*.dist-info')),pathlib.Path('/wheels'),pathlib.Path('/service-wheels'),*list(pathlib.Path('/usr/local/bin').glob('pip*'))]
for p in targets:
 if p.is_dir():shutil.rmtree(p)
 elif p.exists():p.unlink()
'''
INVENTORY = '''import importlib.metadata as m,importlib.util as u,json,pathlib,os
print(json.dumps({'distributions':{d.metadata['Name']:d.version for d in m.distributions()},'pip_present':u.find_spec('pip') is not None,'ensurepip_present':u.find_spec('ensurepip') is not None,'wheel_dirs_present':any(pathlib.Path(p).exists() for p in ['/wheels','/service-wheels']),'uid':os.getuid()}))
'''
CLEANUP = '''import asyncio,hashlib,json,pathlib
from service_validation import connect,storage_client
async def main():
 p=pathlib.Path('/evidence/local-service-validation.json'); r=json.loads(p.read_text()); f=r['fixture']; s=storage_client()
 try:
  c=await connect(); result=await c.get_workflow_handle(f['workflow_id']).result()
  assert result['sha256']==f['sha256']
  data=s.get_object(Bucket='mcpstudio-fixtures',Key=f['key'])['Body'].read()
  assert hashlib.sha256(data).hexdigest()==f['sha256']
  r['checks'].append({'name':'completed workflow and stored bytes readable by fresh candidate process (no restart)','passed':True})
 finally:
  assert f['key'].startswith('readiness/') and len(f['key'])==46
  s.delete_object(Bucket='mcpstudio-fixtures',Key=f['key'])
 from botocore.exceptions import ClientError
 try:s.head_object(Bucket='mcpstudio-fixtures',Key=f['key']);raise AssertionError('fixture remains')
 except ClientError as e:assert e.response['ResponseMetadata']['HTTPStatusCode']==404
 r['checks'].append({'name':'unique fixture object removed','passed':True})
 r['fixture_object_removed']=True;r['restart_phase_complete']=False
 r['scope']='Candidate client workflow/activity/S3 regression against existing local services; no service restart performed'
 p.write_text(json.dumps(r,indent=2)+'\\n');print('Candidate service regression and cleanup passed')
asyncio.run(main())
'''

def main():
    OUT.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((ROOT/'docs/quality/runtime-audit/image-review.json').read_text())
    database=json.loads((ROOT/'work/runtime-audit/cache/db/metadata.json').read_text())
    assert database==baseline['database_metadata'], 'Refresh the baseline before comparing a different advisory database'
    report={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'scope':'Isolated tooling-free Python candidates; no approved pin changes or service restarts',
            'adopted':False,'h04_complete':False,'complete':False,'images':[],
            'same_advisory_database_as_baseline':True,
            'scanner_sha256':hashlib.sha256((ROOT/'work/runtime-audit/trivy.exe').read_bytes()).hexdigest()}
    save(OUT/'assessment.json',report)
    for label,tag in [('worker_fixture','mcpstudio-worker-readiness:0.1.0'),('service_fixture','mcpstudio-service-readiness:0.1.0')]:
        original=inspect(tag); old=next(i for i in baseline['images'] if i['label']==label)
        assert original['Id']==old['image_id'], 'Baseline tag changed; re-review required'
        context=WORK/label; context.mkdir(exist_ok=True)
        (context/'prune.py').write_text(PRUNE,encoding='utf-8')
        config=original['Config']
        # Flatten sanitized filesystem into a fresh final image: original pip/wheels
        # are not retained in final image layers. Preserve baseline runtime config.
        input_tag='mcpstudio-candidate-input:'+original['Id'].split(':')[1]
        run(['docker','tag',original['Id'],input_tag])
        assert inspect(input_tag)['Id']==original['Id']
        dockerfile=f'FROM {input_tag} AS cleaned\nUSER root\nCOPY prune.py /tmp/prune.py\nRUN python /tmp/prune.py && rm /tmp/prune.py\nFROM scratch\nCOPY --from=cleaned / /\n'
        for env in config['Env']:
            key,value=env.split('=',1); dockerfile+=f'ENV {key}={json.dumps(value)}\n'
        dockerfile+='WORKDIR /fixture\nUSER 65534:65534\nCMD '+json.dumps(config['Cmd'])+'\n'
        (context/'Dockerfile').write_text(dockerfile,encoding='utf-8')
        (OUT/(label+'.Dockerfile')).write_text(dockerfile,encoding='utf-8')
        candidate='mcpstudio-'+label.replace('_','-')+'-candidate:pip-free'
        print('Building '+label,flush=True)
        build=run(['docker','build','--network=none','--pull=false','-t',candidate,context],timeout=400)
        (OUT/(label+'-build.log')).write_text(build,encoding='utf-8')
        info=inspect(candidate); image=info['Id']
        assert not set(original['RootFS']['Layers']) & set(info['RootFS']['Layers'])
        before=json.loads(container(original['Id'],['python','-c',INVENTORY]))
        after=json.loads(container(image,['python','-c',INVENTORY]))
        expected={k:v for k,v in before['distributions'].items() if k.lower()!='pip'}
        assert after['distributions']==expected and not after['pip_present'] and not after['ensurepip_present'] and not after['wheel_dirs_present'] and after['uid']==65534
        evidence=OUT/label; evidence.mkdir(exist_ok=True)
        container(image,['python','/fixture/worker-readiness.py'],evidence)
        runtime=json.loads((evidence/'worker-runtime-validation.json').read_text());assert runtime['passed']
        run([sys.executable,'-X','utf8',ROOT/'tools/fixtures/m03/worker-boundary-runner.py',
             '--image',image,'--evidence-dir',evidence])
        boundary=json.loads((evidence/'worker-boundary-validation.json').read_text())
        assert boundary['passed'] and boundary['cleanup_complete']
        entry={'label':label,'baseline_id':original['Id'],'candidate_id':image,'candidate_tag':candidate,
               'architecture':info['Architecture'],'final_layers':len(info['RootFS']['Layers']),
               'baseline_layers_not_in_final_image':True,
               'inventory_before':before,'inventory_after':after,'runtime_checks':len(runtime['checks']),
               'boundary_checks':len(boundary['checks'])}
        if label=='service_fixture':
            envfile=ROOT/'.local/services/fixture.env'
            container(image,['python','/fixture/service_validation.py'],evidence,'mcpstudio-local_default',envfile)
            container(image,['python','-c',CLEANUP],evidence,'mcpstudio-local_default',envfile)
            entry['service_regression']=json.loads((evidence/'local-service-validation.json').read_text())
        print('Scanning '+label,flush=True)
        scan=OUT/(label+'-scan.json')
        run([ROOT/'work/runtime-audit/trivy.exe','image','--cache-dir',ROOT/'work/runtime-audit/cache',
             '--skip-version-check','--skip-db-update','--no-progress','--scanners','vuln','--pkg-types','os,library',
             '--image-src','docker','--docker-host','npipe:////./pipe/dockerDesktopLinuxEngine',
             '--format','json','--output',scan,'--timeout','8m',image],timeout=500)
        raw=json.loads(scan.read_text(encoding='utf-8'))
        findings=[v for r in raw.get('Results',[]) for v in r.get('Vulnerabilities',[])]
        entry.update(baseline_counts=old['severity_counts'],candidate_counts=dict(collections.Counter(v['Severity'] for v in findings)),
                     scan_sha256=hashlib.sha256(scan.read_bytes()).hexdigest(),remaining_findings=len(findings),
                     remaining_library_findings=sum(len(r.get('Vulnerabilities',[])) for r in raw.get('Results',[]) if r.get('Class')=='lang-pkgs'))
        assert inspect(tag)['Id']==original['Id']
        report['images'].append(entry);save(OUT/'assessment.json',report)
    report['database_metadata']=json.loads((ROOT/'work/runtime-audit/cache/db/metadata.json').read_text())
    assert report['database_metadata']==database
    report['validation_check_entries']=sum(e['runtime_checks']+e['boundary_checks']+len(e.get('service_regression',{}).get('checks',[])) for e in report['images'])
    report['complete']=True;save(OUT/'assessment.json',report)
    print(json.dumps({i['label']:i['candidate_counts'] for i in report['images']},indent=2))

if __name__=='__main__':main()
