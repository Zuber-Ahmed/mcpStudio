"""Independent rerun of completed migration 009, with isolated evidence and regression probes."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
runner = Path(__file__).with_name('policy-identity-runner.py')
files = sorted((root / 'infra/database/migrations').glob('00[1-9]_*.sql'))
migration_sources = {p.name: p.read_text() for p in files}
source = runner.read_text()
index = {'completed_thread_turn': '01a188e6-8f80-70f2-83f4-0faee48d0819',
         'runner_sha256': hashlib.sha256(runner.read_bytes()).hexdigest(),
         'migration_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
         'helper_sha256': hashlib.sha256((root / 'tools/plan_payload.py').read_bytes()).hexdigest()}
(root / 'docs/quality/independent-qa/nine-migration-inputs.json').write_text(json.dumps(index, indent=2) + '\n')
source = source.replace("(root/'infra/database/migrations'/filename).read_text()", 'migration_sources[filename]')
source = source.replace("(root/'infra/database/migrations/009_policy_version_identity.sql').read_text()", "migration_sources['009_policy_version_identity.sql']")
source = source.replace("root/'docs/quality/physical-schema-catalog.json'", "root/'docs/quality/independent-qa/nine-migration-catalog.json'")
source = source.replace("root/'docs/quality/policy-identity-validation.json'", "root/'docs/quality/independent-qa/nine-migration-validation.json'")
source = source.replace(" report['passed']=True", ''' reject('QA-02 generation plan hash remains immutable',f"UPDATE run SET plan_hash=repeat('f',64);")
 reject('QA-01 same-tenant different-project snapshot rejected',f"BEGIN;INSERT INTO project(tenant_id,id,name,source) VALUES({T},{U(990)},'QA other project',"+J(dict(kind='local',location='C:/fixture/other'))+f");INSERT INTO analysis(tenant_id,project_id,id,source_digest,snapshot_id,resolved_revision,status,completed_at,analyzer_versions) VALUES({T},{U(990)},{U(991)},repeat('a',64),{U(9)},'r1','succeeded',now(),"+J(versions)+");",'23503')
 report['passed']=True''')
exec(compile(source, str(runner), 'exec'), {'__file__': str(runner), 'migration_sources': migration_sources})
