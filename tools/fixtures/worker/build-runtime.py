from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import urllib.request

root=Path(__file__).resolve().parents[3]
source=Path(__file__).resolve().parent
target=root/'tools/fixtures/worker'
target.mkdir(parents=True,exist_ok=True)
build=root/'work/worker-build'
wheels=build/'wheels'
wheels.mkdir(parents=True,exist_ok=True)
def run(args,timeout=300):
    p=subprocess.run([str(x) for x in args],cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    if p.returncode:
        raise RuntimeError(p.stdout+'\n'+p.stderr)
    return p.stdout.strip()
image_digest=json.loads(run(['docker','image','inspect','python:3.14.10-slim','--format','{{json .RepoDigests}}']))[0]
print('Downloading binary wheels for the selected Linux Python runtime.',flush=True)
download=run(['docker','run','--rm','--mount',f'type=bind,source={wheels},target=/wheels',image_digest,
    'python','-m','pip','download','--only-binary=:all:','--dest','/wheels',
    'temporalio==1.35.0','tree-sitter==0.26.0','tree-sitter-typescript==0.23.2'])
(build/'download.log').write_text(download+'\n',encoding='utf-8')
locked=[]
for wheel in sorted(wheels.glob('*.whl')):
    name,version=wheel.name.split('-')[:2]
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=30) as response:
        metadata=json.load(response)
    entry=next(x for x in metadata['urls'] if x['filename']==wheel.name)
    digest=hashlib.sha256(wheel.read_bytes()).hexdigest()
    if digest!=entry['digests']['sha256']:
        raise RuntimeError('Published wheel hash mismatch: '+wheel.name)
    locked.append({'name':name.replace('_','-'),'version':version,'filename':wheel.name,'sha256':digest})
lock='\n'.join(f"{x['name']}=={x['version']} --hash=sha256:{x['sha256']}" for x in locked)+'\n'
(build/'requirements.lock').write_text(lock,encoding='utf-8')
for name in ['worker-readiness.py','readiness_workflow.py']:
    if (source/name).resolve() != (target/name).resolve():
        shutil.copyfile(source/name,target/name)
    shutil.copyfile(source/name,build/name)
dockerfile=f'''FROM {image_digest}
COPY wheels /wheels
COPY requirements.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels --require-hashes -r /tmp/requirements.lock && python -m pip check
WORKDIR /fixture
COPY worker-readiness.py readiness_workflow.py /fixture/
USER 65534:65534
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["python", "/fixture/worker-readiness.py"]
'''
(build/'Dockerfile').write_text(dockerfile,encoding='utf-8')
shutil.copyfile(build/'Dockerfile',target/'Dockerfile.readiness')
print(f'Verified {len(locked)} wheel hashes against PyPI. Building offline.',flush=True)
tag='mcpstudio-worker-readiness:0.1.0'
buildlog=run(['docker','build','--network','none','--tag',tag,str(build)])
(build/'build.log').write_text(buildlog+'\n',encoding='utf-8')
quality=root/'docs/quality'
args=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL',
    '--security-opt','no-new-privileges','--memory','512m','--cpus','1','--pids-limit','64',
    '--tmpfs','/tmp:rw,noexec,nosuid,size=16m',
    '--mount',f'type=bind,source={quality},target=/evidence',tag]
print('Running trusted parser and Temporal sandbox fixture without network.',flush=True)
output=run(args,timeout=90)
print(output,flush=True)
report=json.loads((quality/'worker-runtime-validation.json').read_text())
if not report['passed']:
    raise RuntimeError('Worker runtime fixture failed')
shutil.copyfile(build/'requirements.lock',root/'apps/workers/requirements.linux-amd64.lock')
(quality/'worker-wheel-manifest.json').write_text(json.dumps({'base_image':image_digest,'wheels':locked,
    'all_hashes_verified_against_pypi':True,'offline_image_build':True,'fixture_image_id':run(['docker','image','inspect',tag,'--format','{{.Id}}'])},indent=2)+'\n',encoding='utf-8')
project=root/'apps/workers/pyproject.toml'
s=project.read_text(encoding='utf-8').replace('dependencies = []','dependencies = [\n  "temporalio==1.35.0",\n  "tree-sitter==0.26.0",\n  "tree-sitter-typescript==0.23.2",\n]')
s=s.replace('status = "scaffold-only"','status = "runtime-readiness-verified; application-analyzers-not-implemented"')
project.write_text(s,encoding='utf-8')
status=root/'docs/planning/STATUS.md'
s=status.read_text(encoding='utf-8')
update='''## Worker runtime update — 29 October 2026

Selected Python 3.14.10 verified in the approved Linux-container worker model. Temporal SDK 1.35.0, tree-sitter 0.26.0 and TypeScript grammar 0.23.2 pinned. All resolved Linux wheel hashes checked against PyPI; offline build and network-disabled parser/Temporal sandbox readiness fixture passed. See docs/quality/worker-runtime-validation.json and worker-wheel-manifest.json. Native Windows Python installer failed before runtime installation; no fallback to older Python used for worker evidence.

This completes worker runtime/package readiness only. It does not implement application analyzers or prove workflow execution against a Temporal server. Remaining main work packages: local Temporal/storage services and final readiness validation.

'''
if '## Worker runtime update' not in s:
    s=s.replace('# Current project status\n','# Current project status\n\n'+update,1)
status.write_text(s,encoding='utf-8')
print('Saved locked worker dependencies, image digest and current readiness evidence.',flush=True)
