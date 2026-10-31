"""Scan only pinned trusted foundation image IDs; no source/credential directories."""
from pathlib import Path
import collections,datetime,hashlib,json,subprocess
root=Path(__file__).resolve().parents[2];work=root/'work/runtime-audit';q=root/'docs/quality/runtime-audit';out=q/'images';out.mkdir(parents=True,exist_ok=True)
scanner=work/'trivy.exe';cache=work/'cache'
def run(args,timeout=180):return subprocess.run([str(x) for x in args],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def save(data):
 (q/'image-review.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
services=json.loads((root/'docs/quality/local-service-images.json').read_text())['images']
worker=json.loads((root/'docs/quality/worker-wheel-manifest.json').read_text())
targets=dict(services,python_base=worker['base_image'],worker_fixture='mcpstudio-worker-readiness:0.1.0',service_fixture='mcpstudio-service-readiness:0.1.0',sandbox_smoke='alpine:3.22.2')
report={'recorded_date':'2026-10-30','scanner':'Trivy 0.76.1','scope':'Pinned local trusted foundation images; OS/library vulnerability scan only, not secret/license/misconfiguration/reachability assessment',
 'sources':['https://trivy.dev/docs/dev/guide/target/container_image/','https://github.com/aquasecurity/trivy/releases/tag/v0.76.1'],
 'database_ready':False,'images':[],'complete':False}
print('Refreshing local vulnerability database.',flush=True)
p=run([scanner,'image','--cache-dir',cache,'--skip-version-check','--no-progress','--download-db-only','--timeout','3m'],timeout=200)
(q/'database-update.log').write_text(p.stderr+'\n'+p.stdout,encoding='utf-8')
if p.returncode:
 report['database_error']=p.stderr[-2500:];save(report);print('Image scanning blocked: advisory database unavailable.',flush=True);raise SystemExit(1)
report['database_ready']=True
db=cache/'db/metadata.json'
if db.exists():report['database_metadata']=json.loads(db.read_text());report['database_metadata_sha256']=hashlib.sha256(db.read_bytes()).hexdigest()
save(report)
for label,ref in targets.items():
 print('Scanning trusted local image: '+label,flush=True)
 inspect=run(['docker','image','inspect',ref,'--format','{{json .}}'])
 entry={'label':label,'requested_reference':ref,'complete':False}
 if inspect.returncode:
  entry['error']='Pinned local image missing';report['images'].append(entry);save(report);continue
 info=json.loads(inspect.stdout);entry.update(image_id=info['Id'],repo_digests=info.get('RepoDigests',[]),os=info['Os'],architecture=info['Architecture'])
 path=out/(label+'.json')
 args=[scanner,'image','--cache-dir',cache,'--skip-version-check','--skip-db-update','--no-progress','--scanners','vuln','--pkg-types','os,library',
 '--image-src','docker','--docker-host','npipe:////./pipe/dockerDesktopLinuxEngine','--format','json','--output',path,'--timeout','8m',info['Id']]
 try:p=run(args,timeout=500)
 except subprocess.TimeoutExpired:
  entry['error']='Scanner deadline exceeded';report['images'].append(entry);save(report);continue
 (out/(label+'.log')).write_text(p.stderr+'\n'+p.stdout,encoding='utf-8')
 entry['exit_code']=p.returncode
 if p.returncode or not path.exists():entry['error']=p.stderr[-2500:]
 else:
  data=json.loads(path.read_text(encoding='utf-8'));findings=[];packages=0
  for result in data.get('Results',[]):
   packages+=len(result.get('Packages',[]))
   for v in result.get('Vulnerabilities',[]):
    findings.append({'id':v['VulnerabilityID'],'package':v.get('PkgName'),'installed':v.get('InstalledVersion'),
     'fixed':v.get('FixedVersion',''),'severity':v.get('Severity'),'status':v.get('Status'),'type':result.get('Type'),
     'target':result.get('Target'),'title':v.get('Title'),'primary_url':v.get('PrimaryURL')})
  entry.update(complete=True,report_path='docs/quality/runtime-audit/images/'+path.name,report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
   severity_counts=dict(collections.Counter(v['severity'] for v in findings)),findings_count=len(findings),package_entries=packages,
   fixable_findings=sum(bool(v['fixed']) for v in findings),findings=findings,os_metadata=data.get('Metadata',{}).get('OS'))
  print(label+': '+str(entry['severity_counts'])+'; packages '+str(packages),flush=True)
 report['images'].append(entry);save(report)
report['complete']=len(report['images'])==len(targets) and all(i['complete'] for i in report['images'])
report['no_known_vulnerabilities_returned']=report['complete'] and not any(i.get('findings_count',0) for i in report['images'])
save(report)
print('Image scan finished. complete='+str(report['complete']),flush=True)
