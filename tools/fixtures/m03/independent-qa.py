"""Independent QA: isolated DB probes; never modifies the running service stack."""
import json
from pathlib import Path
import secrets
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
name = 'mcpstudio-qa-' + uuid.uuid4().hex[:12]
image = json.loads((ROOT / 'infra/compose.yaml').read_text())['services']['postgres']['image']
report = {'image': image, 'checks': [], 'scope': 'Disposable prototype only; no product database'}

def run(args, data=None):
    return subprocess.run(args, input=data, capture_output=True, text=True, timeout=60)

try:
    p = run(['docker', 'run', '-d', '--rm', '--name', name, '--network', 'none',
             '--memory', '512m', '--cpus', '1', '--tmpfs', '/var/lib/postgresql/data:rw,size=512m',
             '-e', 'POSTGRES_PASSWORD=' + secrets.token_urlsafe(32), image])
    if p.returncode:
        raise RuntimeError(p.stderr)
    for _ in range(30):
        if run(['docker', 'exec', name, 'pg_isready', '-U', 'postgres']).returncode == 0:
            break
        time.sleep(1)
    def sql(statement):
        return run(['docker', 'exec', '-i', name, 'psql', '-U', 'postgres', '-qAt',
                    '-v', 'ON_ERROR_STOP=1'], statement)
    original = sql(Path(__file__).with_name('database-fixture.sql').read_text())
    if original.returncode:
        raise RuntimeError(original.stderr)
    baseline = json.loads(next(x for x in reversed(original.stdout.splitlines()) if x.startswith('{')))
    report['baseline'] = baseline
    probes = [
        ('analysis rejects another project snapshot in the same tenant', '''
         SET search_path=fixture;
         INSERT INTO project VALUES(ident(300),ident(1));
         INSERT INTO analysis VALUES(ident(301),ident(1),ident(300),ident(20));
        '''),
        ('generation cannot change approved hash after admission', '''
         SET search_path=fixture;
         UPDATE generation SET plan_hash=repeat('f',64) WHERE id=ident(90);
        ''')
    ]
    for label, statement in probes:
        p = sql('BEGIN;\n' + statement + '\nROLLBACK;')
        report['checks'].append({'name': label, 'passed': p.returncode != 0,
                                 'sql_exit_code': p.returncode, 'stderr': p.stderr.strip()})
except Exception as ex:
    report['error'] = str(ex)
finally:
    run(['docker', 'rm', '-f', name])
    absent = run(['docker', 'ps', '-a', '--filter', 'name=^/' + name + '$', '--format', '{{.Names}}'])
    report['fixture_removed'] = absent.returncode == 0 and not absent.stdout.strip()
    (ROOT / 'docs/quality/independent-qa/database-probes.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
raise SystemExit(0 if not report.get('error') and report.get('baseline', {}).get('passed')
                 and report.get('fixture_removed') and len(report['checks']) == 2
                 and all(c['passed'] for c in report['checks']) else 1)
