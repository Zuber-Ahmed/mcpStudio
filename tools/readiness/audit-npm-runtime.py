from pathlib import Path
import json,subprocess,hashlib,datetime,os
root=Path(__file__).resolve().parents[2];q=root/'docs/quality/runtime-audit';q.mkdir(parents=True,exist_ok=True)
node=root/'work/runtimes/node-v26.13.0-win-x64/node.exe';npm=node.parent/'node_modules/npm/bin/npm-cli.js'
summary=[]
for folder,label in [('node-tools','contract-tools'),('mcp-fixture','mcp-fixture')]:
 cwd=root/'work'/folder
 p=subprocess.run([str(node),str(npm),'audit','--json','--ignore-scripts'],cwd=cwd,capture_output=True,text=True,timeout=120)
 try:data=json.loads(p.stdout)
 except Exception:data={'error':{'message':'Audit returned no JSON'},'stderr':p.stderr[-1500:]}
 (q/(label+'-audit.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
 summary.append({'label':label,'exit_code':p.returncode,'query_succeeded':not bool(data.get('error')) and bool(data.get('metadata')),
 'vulnerabilities':data.get('metadata',{}).get('vulnerabilities'),
 'lock_sha256':hashlib.sha256((cwd/'package-lock.json').read_bytes()).hexdigest(),'package_lock':'work/'+folder+'/package-lock.json',
 'dependencies':json.loads((cwd/'package.json').read_text()).get('dependencies',{})})
report={'recorded_date':'2026-10-30','scope':'Installed isolated contract/MCP fixture npm dependency locks; no fix/install or uninitialized app dependency claim','audits':summary}
(q/'npm-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
