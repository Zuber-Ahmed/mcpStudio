"""Compare isolated Debian OS candidates; do not adopt tags or touch service data."""
from pathlib import Path
import collections, datetime, hashlib, importlib.util, json, subprocess, sys

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('candidate_helpers',Path(__file__).with_name('evaluate-python-runtime-candidates.py'))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
OUT=ROOT/'docs/quality/runtime-candidates/python-os'
WORK=ROOT/'work/runtime-candidates/python-os'
BOOKWORM='python@sha256:516b51cb9db2ef061e465c803e50f64361b82cefd91e525b889b967b83e83527'
TRIXIE='python@sha256:3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999'

def scan(image,path):
 h.run([ROOT/'work/runtime-audit/trivy.exe','image','--cache-dir',ROOT/'work/runtime-audit/cache',
        '--skip-version-check','--skip-db-update','--no-progress','--scanners','vuln','--pkg-types','os,library',
        '--image-src','docker','--docker-host','npipe:////./pipe/dockerDesktopLinuxEngine',
        '--format','json','--output',path,'--timeout','8m',image],timeout=500)
 raw=json.loads(path.read_text(encoding='utf-8'))
 findings=[v for r in raw.get('Results',[]) for v in r.get('Vulnerabilities',[])]
 return {'counts':dict(collections.Counter(v['Severity'] for v in findings)),
         'findings':len(findings),'fixable':sum(bool(v.get('FixedVersion')) for v in findings),
         'library_findings':sum(len(r.get('Vulnerabilities',[])) for r in raw.get('Results',[]) if r.get('Class')=='lang-pkgs'),
         'os':raw['Metadata'].get('OS'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
 OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
 prior=json.loads((ROOT/'docs/quality/runtime-candidates/python-tooling-free/assessment.json').read_text())
 database=json.loads((ROOT/'work/runtime-audit/cache/db/metadata.json').read_text())
 assert database==prior['database_metadata']
 worker=next(e for e in prior['images'] if e['label']=='worker_fixture')
 baseline=h.inspect(worker['candidate_id']);original=h.inspect(worker['baseline_id'])
 assert h.inspect('mcpstudio-worker-readiness:0.1.0')['Id']==original['Id']
 report={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'adopted':False,'complete':False,
         'scope':'Python worker Debian OS candidate evaluation; no service restart or server/database changes',
         'database_metadata':database,'baseline_id':baseline['Id'],'baseline_counts':worker['candidate_counts'],
         'sources':['https://raw.githubusercontent.com/docker-library/official-images/master/library/python',
                    'https://security-tracker.debian.org/tracker/'],
         'scanner_sha256':hashlib.sha256((ROOT/'work/runtime-audit/trivy.exe').read_bytes()).hexdigest(),'candidates':[]}
 # Verify pulled official candidates and original runtime version, retaining digests.
 for name,ref in [('trixie',TRIXIE),('bookworm',BOOKWORM)]:
  info=h.inspect(ref);report[name+'_base']={'reference':ref,'image_id':info['Id'],'architecture':info['Architecture']}
  assert info['Architecture']=='amd64'
  assert '3.14.10' in h.container(info['Id'],['python','--version'])
 report['trixie_refresh_unchanged']=h.inspect('python:3.14.10-slim-trixie')['Id']==h.inspect(TRIXIE)['Id']
 h.save(OUT/'assessment.json',report)
 for label in ['trixie_apt_upgrade','bookworm']:
  context=WORK/label;context.mkdir(exist_ok=True)
  (context/'prune.py').write_text(h.PRUNE,encoding='utf-8')
  if label=='trixie_apt_upgrade':
   alias='mcpstudio-os-input:'+baseline['Id'].split(':')[1];h.run(['docker','tag',baseline['Id'],alias])
   head=f'FROM {alias} AS cleaned\nUSER root\n'
   # Debian's signed repositories select upgrades; preserve actual pre/post inventories.
   head+='RUN mkdir -p /opt/os-review && dpkg-query -W > /opt/os-review/os-before.tsv && apt-get update && apt-get -y upgrade && dpkg-query -W > /opt/os-review/os-after.tsv && rm -rf /var/lib/apt/lists/*\n'
  else:
   alias='mcpstudio-os-input:'+original['Id'].split(':')[1];h.run(['docker','tag',original['Id'],alias])
   head=f'FROM {alias} AS wheel_source\nFROM {BOOKWORM} AS cleaned\n'
   head+='COPY --from=wheel_source /wheels /wheels\nCOPY --from=wheel_source /tmp/requirements.lock /tmp/requirements.lock\n'
   head+='RUN python -m pip install --no-index --no-cache-dir --find-links=/wheels --require-hashes -r /tmp/requirements.lock && python -m pip check\n'
   head+='COPY --from=wheel_source /fixture /fixture\nCOPY prune.py /tmp/prune.py\nRUN python /tmp/prune.py && rm /tmp/prune.py\n'
  recipe=head+'FROM scratch\nCOPY --from=cleaned / /\n'
  for env in baseline['Config']['Env']:
   k,v=env.split('=',1);recipe+=f'ENV {k}={json.dumps(v)}\n'
  recipe+='WORKDIR /fixture\nUSER 65534:65534\nCMD ["python", "/fixture/worker-readiness.py"]\n'
  (context/'Dockerfile').write_text(recipe,encoding='utf-8');(OUT/(label+'.Dockerfile')).write_text(recipe,encoding='utf-8')
  tag='mcpstudio-worker-os-candidate:'+label.replace('_','-')
  print('Building '+label,flush=True)
  cmd=['docker','build','--pull=false','--progress=plain','--network='+('default' if label=='trixie_apt_upgrade' else 'none'),'-t',tag,context]
  p=subprocess.run([str(a) for a in cmd],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=500)
  (OUT/(label+'-build.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
  if p.returncode:raise RuntimeError(p.stderr[-2500:])
  info=h.inspect(tag);image=info['Id'];entry={'label':label,'image_id':image,'tag':tag,'adopted':False}
  inv=json.loads(h.container(image,['python','-c',h.INVENTORY]))
  assert inv==worker['inventory_after'];entry['inventory']=inv
  if label=='trixie_apt_upgrade':
   before=h.container(image,['cat','/opt/os-review/os-before.tsv']);after=h.container(image,['cat','/opt/os-review/os-after.tsv'])
   (OUT/'packages-before.tsv').write_text(before);(OUT/'packages-after.tsv').write_text(after)
   b=dict(line.split('\t',1) for line in before.splitlines());a=dict(line.split('\t',1) for line in after.splitlines())
   entry['changed_packages']={k:{'before':b.get(k),'after':v} for k,v in a.items() if b.get(k)!=v}
  evidence=OUT/label;evidence.mkdir(exist_ok=True)
  h.container(image,['python','/fixture/worker-readiness.py'],evidence)
  runtime=json.loads((evidence/'worker-runtime-validation.json').read_text());assert runtime['passed'];entry['runtime_checks']=len(runtime['checks'])
  h.run([sys.executable,'-X','utf8',ROOT/'tools/fixtures/m03/worker-boundary-runner.py','--image',image,'--evidence-dir',evidence])
  boundary=json.loads((evidence/'worker-boundary-validation.json').read_text());assert boundary['passed'];entry['boundary_checks']=len(boundary['checks'])
  print('Scanning '+label,flush=True);entry['scan']=scan(image,OUT/(label+'-scan.json'))
  report['candidates'].append(entry);h.save(OUT/'assessment.json',report)
 assert h.inspect('mcpstudio-worker-readiness:0.1.0')['Id']==original['Id']
 assert json.loads((ROOT/'work/runtime-audit/cache/db/metadata.json').read_text())==database
 report['complete']=True;report['h04_complete']=False
 h.save(OUT/'assessment.json',report)
 print(json.dumps([(c['label'],c['scan'],c.get('changed_packages')) for c in report['candidates']],indent=2))

if __name__=='__main__':main()
