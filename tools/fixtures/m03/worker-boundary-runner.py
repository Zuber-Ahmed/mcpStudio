from pathlib import Path
import json, subprocess, tempfile, uuid, shutil, hashlib, datetime, argparse
root=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser()
parser.add_argument('--image',default='mcpstudio-worker-readiness:0.1.0')
parser.add_argument('--evidence-dir',type=Path,default=root/'docs/quality')
options=parser.parse_args()
quality=options.evidence_dir.resolve(); quality.mkdir(parents=True,exist_ok=True)
checks=[]
def run(args,timeout=60):
 return subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=timeout)
def check(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok: raise RuntimeError(name)
image=options.image
name='mcpstudio-bounds-'+uuid.uuid4().hex
parent=root/'work'; parent.mkdir(exist_ok=True)
folder=Path(tempfile.mkdtemp(prefix='readiness-bounds-',dir=parent)).resolve()
assert folder.parent==parent.resolve() and folder.name.startswith('readiness-bounds-')
source=folder/'source'; output=folder/'output'; source.mkdir(); output.mkdir()
canary=source/'canary.txt'; canary.write_text('trusted fixture only')
before=hashlib.sha256(canary.read_bytes()).hexdigest()
code='''import pathlib,socket,json,os
results={}
for label,path in [('source_read_only','/source/canary.txt'),('root_read_only','/escape.txt')]:
 try:
  pathlib.Path(path).write_text('unexpected'); results[label]=False
 except OSError: results[label]=True
try:
 socket.create_connection(('1.1.1.1',443),timeout=2); results['egress_denied']=False
except OSError: results['egress_denied']=True
results['non_root']=os.getuid()==65534
pathlib.Path('/output/fixture.txt').write_text('bounded output')
results['output_writable']=True
pathlib.Path('/tmp/fixture-link').symlink_to('/source/canary.txt')
try:
 pathlib.Path('/tmp/fixture-link').write_text('unexpected'); results['symlink_target_read_only']=False
except OSError: results['symlink_target_read_only']=True
pathlib.Path('/output/results.json').write_text(json.dumps(results))
print(json.dumps(results))
'''
base=['docker','run','--rm','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user','65534:65534','--memory','128m','--cpus','0.5','--pids-limit','32','--tmpfs','/tmp:rw,noexec,nosuid,size=8m']
try:
 p=run(base+['--mount',f'type=bind,source={source},target=/source,readonly','--mount',f'type=bind,source={output},target=/output',image,'python','-c',code])
 check('bounded container fixture exits successfully',p.returncode==0)
 for key,value in json.loads((output/'results.json').read_text()).items():check(key,value)
 check('host source digest unchanged',hashlib.sha256(canary.read_bytes()).hexdigest()==before)
 # Keep this trusted sleep alive until the orchestrator forces its deadline.
 p=run(['docker','run','-d','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','128m','--cpus','0.5','--pids-limit','32','--tmpfs','/tmp:rw,noexec,nosuid,size=8m',image,'python','-c','import pathlib,time; pathlib.Path("/tmp/timeout-canary").write_text("ephemeral"); time.sleep(120)'])
 check('timeout fixture starts',p.returncode==0)
 info=json.loads(run(['docker','inspect',name]).stdout)[0]
 host=info['HostConfig']
 check('memory CPU process limits applied',host['Memory']==134217728 and host['NanoCpus']==500000000 and host['PidsLimit']==32)
 try:
  run(['docker','wait',name],timeout=3)
  check('forced deadline occurs',False)
 except subprocess.TimeoutExpired:check('forced deadline occurs',True)
 p=run(['docker','rm','-f',name]); check('timed out container forcibly removed',p.returncode==0)
 check('no retained container or ephemeral tmp filesystem',run(['docker','inspect',name]).returncode!=0)
finally:
 run(['docker','rm','-f',name])
 assert folder.parent==parent.resolve() and folder.name.startswith('readiness-bounds-')
 shutil.rmtree(folder)
check('unique host fixture directory removed',not folder.exists())
report={'recorded_date':datetime.date.today().isoformat(),'image':image,'scope':'Trusted Docker isolation/resource/forced deadline fixture, not application path validator or hostile-code sandbox certification','passed':all(c['passed'] for c in checks),'checks':checks,'limits':{'memory_bytes':134217728,'cpu':0.5,'pids':32,'deadline_seconds':3},'cleanup_complete':True}
(quality/'worker-boundary-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
