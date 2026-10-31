"""Freeze and rerun completed six-migration suite without replacing engineer evidence."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
runner = Path(__file__).with_name('metadata-chain-runner.py')
names = ['001_admission_kernel.sql', '002_bound_validation.sql', '003_runtime_roles.sql',
         '004_source_graph_recommendation.sql', '005_artifacts_findings_revocations.sql',
         '006_identity_approval_metadata.sql']
migration_sources = {n: (root / 'infra/database/migrations' / n).read_text() for n in names}
source = runner.read_text()
index = {'completed_thread_turn': '01a188cd-21d3-75f3-99a8-95cbb0f420ea',
         'runner_sha256': hashlib.sha256(runner.read_bytes()).hexdigest(),
         'migration_sha256': {n: hashlib.sha256((root / 'infra/database/migrations' / n).read_bytes()).hexdigest() for n in names}}
(root / 'docs/quality/independent-qa/six-migration-inputs.json').write_text(json.dumps(index, indent=2) + '\n')
source = source.replace("(root/'infra/database/migrations'/filename).read_text()", 'migration_sources[filename]')
source = source.replace("root/'docs/quality/physical-schema-catalog.json'", "root/'docs/quality/independent-qa/six-migration-catalog.json'")
source = source.replace("root/'docs/quality/metadata-chain-validation.json'", "root/'docs/quality/independent-qa/six-migration-validation.json'")
source = source.replace(" report['passed']=True", ''' reject('QA-02 generation approval hash mutation denied',f"UPDATE run SET plan_hash=repeat('f',64) WHERE id='{rid}';")
 report['passed']=True''')
exec(compile(source, str(runner), 'exec'), {'__file__': str(runner), 'migration_sources': migration_sources})
