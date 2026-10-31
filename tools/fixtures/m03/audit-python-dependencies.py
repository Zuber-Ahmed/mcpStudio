from pathlib import Path
import json,urllib.request,datetime
root=Path(__file__).resolve().parents[3]; q=root/'docs/quality'
packages={}
for x in json.loads((q/'worker-wheel-manifest.json').read_text())['wheels']:packages[x['name']]=x['version']
for x in json.loads((q/'local-service-images.json').read_text())['fixture_sdk_wheels']:packages[x['name']]=x['version']
for line in (q/'contract-tools.requirements.txt').read_text().splitlines():
 if '==' in line:
  name,version=line.split('=='); packages[name]=version
packages={name.lower().replace('_','-').replace('.','-'):version for name,version in packages.items()}
items=sorted(packages.items())
body={'queries':[{'package':{'name':n,'ecosystem':'PyPI'},'version':v} for n,v in items]}
report={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'https://api.osv.dev/v1/querybatch','scope':'Exact Python worker/service/contract-tool package versions; excludes OS/container layers, JavaScript and uninstalled frontend packages','packages':[]}
try:
 request=urllib.request.Request(report['source'],data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(request,timeout=45) as response:results=json.load(response)['results']
 assert len(results)==len(items)
 for (name,version),result in zip(items,results):report['packages'].append({'name':name,'version':version,'advisory_ids':[v['id'] for v in result.get('vulns',[])]})
 report['query_succeeded']=True
 report['advisory_count']=sum(len(p['advisory_ids']) for p in report['packages'])
 report['no_known_advisories_returned']=report['advisory_count']==0
except Exception as ex:
 report['query_succeeded']=False;report['error']=str(ex)
(q/'python-dependency-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
