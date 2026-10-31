from pathlib import Path
import json,subprocess
root=Path(__file__).resolve().parents[2];q=root/'docs/quality/runtime-audit'
code='''import importlib.metadata as m,json,pathlib
result={'top_level':{},'pip_vendor_requirements':[],'embedded_sbom_components':[]}
for name in ['pip','urllib3','setuptools','msgpack']:
 try:result['top_level'][name]=m.version(name)
 except m.PackageNotFoundError:result['top_level'][name]=None
base=pathlib.Path('/usr/local/lib/python3.14/site-packages/pip/_vendor')
vendor=base/'vendor.txt'
if vendor.exists():result['pip_vendor_requirements']=[line for line in vendor.read_text().splitlines() if any(x in line.lower() for x in ['urllib3','msgpack','setuptools'])]
for path in pathlib.Path('/usr/local/lib/python3.14').rglob('bom.cdx.json'):
 try:doc=json.loads(path.read_text())
 except Exception:continue
 for c in doc.get('components',[]):
  if c.get('name') in ['urllib3','msgpack','setuptools']:
   result['embedded_sbom_components'].append({'sbom_path':str(path),'name':c['name'],'version':c.get('version'),'purl':c.get('purl'),'properties':c.get('properties',[])})
result['vendor_module_paths']={name:(base/name).exists() for name in ['urllib3','msgpack','pkg_resources']}
print(json.dumps(result))
'''
result={'scope':'Read-only no-network trusted image inventory corroboration; top-level absence does not prove vendored-code non-reachability','images':[]}
for label,image in [('python_base',json.loads((root/'docs/quality/worker-wheel-manifest.json').read_text())['base_image']),('service_fixture','mcpstudio-service-readiness:0.1.0')]:
 p=subprocess.run(['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','128m','--pids-limit','32','--user','65534:65534','--entrypoint','python',image,'-c',code],cwd=root,capture_output=True,text=True,timeout=60)
 entry={'label':label,'complete':p.returncode==0}
 if p.returncode:entry['error']=p.stderr[-1500:]
 else:entry.update(json.loads(p.stdout))
 result['images'].append(entry)
p=subprocess.run(['docker','inspect','mcpstudio-local-schema-1','--format','{{json .State}}'],cwd=root,capture_output=True,text=True,timeout=15)
if p.returncode==0:
 state=json.loads(p.stdout);result['schema_tool_container']={'running':state['Running'],'exit_code':state['ExitCode'],'status':state['Status']}
(q/'inventory-corroboration.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
