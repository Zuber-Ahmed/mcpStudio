from pathlib import Path
import hashlib,json,subprocess,tarfile,urllib.request
root=Path(__file__).resolve().parents[2];q=root/'docs/quality/runtime-audit';work=root/'work/runtime-audit'
checks=[]
for folder,saved in [('node-tools','contract-tools'),('mcp-fixture','mcp-fixture')]:
 a=root/'work'/folder/'package-lock.json';b=root/'docs/quality'/(saved+'.package-lock.json')
 checks.append({'name':saved+' installed lock matches preserved lock','passed':a.read_bytes()==b.read_bytes(),'sha256':hashlib.sha256(a.read_bytes()).hexdigest()})
for manifest,folder,key in [('worker-wheel-manifest.json','worker-build','wheels'),('local-service-images.json','service-fixture-build','fixture_sdk_wheels')]:
 data=json.loads((root/'docs/quality'/manifest).read_text())
 for item in data[key]:
  files=list((root/'work'/folder/'wheels').glob(item['name'].replace('-','_')+'-'+item['version']+'-*.whl'))
  if not files:files=list((root/'work'/folder/'wheels').glob(item['name']+'-'+item['version']+'-*.whl'))
  checks.append({'name':item['name']+' '+item['version']+' wheel retains pinned digest','passed':len(files)==1 and hashlib.sha256(files[0].read_bytes()).hexdigest()==item['sha256']})
integrity={'recorded_date':'2026-10-30','scope':'Previously source-verified installed fixture locks and downloaded binary wheels; no authenticity beyond recorded source checks','checks':checks,'passed':all(c['passed'] for c in checks)}
(q/'lock-integrity.json').write_text(json.dumps(integrity,indent=2)+'\n',encoding='utf-8')
print('Lock/wheel integrity: '+str(integrity['passed'])+' ('+str(len(checks))+' entries)',flush=True)
report={'recorded_date':'2026-10-30','scope':'Selected Node core advisory ranges and Go stdlib/toolchain OSV; not symbol reachability or full host OS audit','node':{'version':'26.13.0','complete':False},'go':{'version':'1.27.3','complete':False}}
try:
 source='https://api.github.com/repos/nodejs/security-wg/git/trees/main?recursive=1'
 with urllib.request.urlopen(source,timeout=30) as response:tree=json.load(response)
 commit=tree['sha'];archive=work/'node-security-wg.tar.gz'
 urllib.request.urlretrieve(f'https://codeload.github.com/nodejs/security-wg/tar.gz/{commit}',archive)
 entries=[]
 with tarfile.open(archive) as t:
  for member in t:
   if '/vuln/core/' in member.name and member.name.endswith('.json') and not member.name.endswith('/index.json') and member.isfile():
    assert member.size<2_000_000
    with t.extractfile(member) as f:value=json.load(f)
    entries.append({'path':member.name,'record':value})
 assert entries,'No Node core advisory entries'
 datafile=work/'node-core-ranges.json';datafile.write_text(json.dumps(entries),encoding='utf-8')
 script=work/'check-node-ranges.cjs'
 script.write_text('''const fs=require('node:fs');const path=require('node:path');
const semver=require(path.resolve('work/runtimes/node-v26.13.0-win-x64/node_modules/npm/node_modules/semver'));
const entries=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let findings=[],unparsed=[];
for(const e of entries){const v=e.record;if(!v.vulnerable || !semver.validRange(v.vulnerable) || (v.patched && !semver.validRange(v.patched))){unparsed.push(e.path);continue;}
if(semver.satisfies('26.13.0',v.vulnerable) && !(v.patched && semver.satisfies('26.13.0',v.patched)))findings.push(v);}
process.stdout.write(JSON.stringify({entries:entries.length,findings,unparsed}));
''',encoding='utf-8')
 p=subprocess.run([str(root/'work/runtimes/node-v26.13.0-win-x64/node.exe'),str(script),str(datafile)],cwd=root,capture_output=True,text=True,timeout=60,check=True)
 node=json.loads(p.stdout);report['node'].update(node,complete=not node['unparsed'],source=source,repository_commit=commit,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
except Exception as ex:report['node']['error']=str(ex)
try:
 request=urllib.request.Request('https://api.osv.dev/v1/querybatch',data=json.dumps({'queries':[{'package':{'name':name,'ecosystem':'Go'},'version':'1.27.3'} for name in ['stdlib','toolchain']]}).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(request,timeout=45) as response:results=json.load(response)['results']
 assert len(results)==2
 report['go'].update(complete=True,queries=[{'package':name,'advisory_ids':[v['id'] for v in entry.get('vulns',[])]} for name,entry in zip(['stdlib','toolchain'],results)],source='https://api.osv.dev/v1/querybatch')
except Exception as ex:report['go']['error']=str(ex)
(q/'core-runtime-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
