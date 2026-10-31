"""Disposable PostgreSQL constraint prototype, not a product migration."""
import json
from pathlib import Path
import secrets
import subprocess
import time
import uuid

root=Path(__file__).resolve().parents[3]
container='mcpstudio-m03-db-'+uuid.uuid4().hex[:10]
image='postgres:17.11'
def run(args, data=None, timeout=60):
    result=subprocess.run(args,cwd=root,input=data,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    return result
report={'scope':'Prototype constraints in disposable database; no application migration or API enforcement proof',
        'image':image,'published_ports':False,'project_data_mounted':False,'passed':False}
try:
    image_result=run(['docker','image','inspect',image,'--format','{{json .RepoDigests}}'])
    if image_result.returncode:
        raise RuntimeError('Selected database image is not present')
    report['image_digest']=json.loads(image_result.stdout)
    started=run(['docker','run','-d','--rm','--name',container,'--network','none','--memory','512m','--cpus','1',
        '--tmpfs','/var/lib/postgresql/data:rw,size=512m','-e','POSTGRES_PASSWORD='+secrets.token_urlsafe(32),image])
    if started.returncode:
        raise RuntimeError(started.stderr)
    ready=False
    for _ in range(30):
        probe=run(['docker','exec',container,'pg_isready','-U','postgres'],timeout=5)
        if probe.returncode==0:
            ready=True;break
        time.sleep(1)
    if not ready:
        raise RuntimeError('Disposable database did not become ready within 30 probes')
    version=run(['docker','exec',container,'psql','-U','postgres','-tA','-c','SHOW server_version;'])
    report['server_version']=version.stdout.strip()
    sql=Path(__file__).with_name('database-fixture.sql').read_text(encoding='utf-8')
    result=run(['docker','exec','-i',container,'psql','-U','postgres','-qAt','-v','ON_ERROR_STOP=1'],data=sql,timeout=60)
    report['sql_exit_code']=result.returncode
    if result.returncode:
        raise RuntimeError(result.stderr)
    payload=next(line for line in reversed(result.stdout.splitlines()) if line.startswith('{'))
    report.update(json.loads(payload))
except Exception as ex:
    report['error']=str(ex)
finally:
    cleanup=run(['docker','rm','--force',container])
    # Remove only the exact uniquely named fixture created by this invocation.
    absent=run(['docker','ps','--all','--filter','name=^/'+container+'$','--format','{{.Names}}'])
    report['fixture_removed']=absent.returncode==0 and not absent.stdout.strip()
    report['passed']=report['passed'] and report['fixture_removed']
    (root/'docs/quality/database-constraint-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
