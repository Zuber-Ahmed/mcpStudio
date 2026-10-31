"""Check claimed logical mappings against the independently captured nine-migration catalog."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
catalog = json.loads((root / 'docs/quality/independent-qa/nine-migration-catalog.json').read_text())
mapping = json.loads((root / 'docs/quality/physical-model-mapping.json').read_text())
logical = json.loads((root / 'packages/contracts/specs/data-dictionary.json').read_text())['entities']
columns = {(c['table'], c['column']) for c in catalog['columns']}
failures = []
seen = set()
count = 0
for row in mapping['entities']:
    entity = row['logical_entity']
    seen.add(entity)
    if set(row['mapped_fields']) != set(logical[entity]):
        failures.append(entity + ': missing logical fields')
    for field, target in row['mapped_fields'].items():
        count += 1
        if (target['table'], target['column']) not in columns:
            failures.append(entity + '.' + field + ': target absent from independent catalog')
if seen != set(logical):
    failures.append('entity inventory differs')
inputs = json.loads((root / 'docs/quality/independent-qa/nine-migration-inputs.json').read_text())
for name, expected in inputs['migration_sha256'].items():
    if hashlib.sha256((root / 'infra/database/migrations' / name).read_bytes()).hexdigest() != expected:
        failures.append('migration changed during review: ' + name)
report = {'passed': not failures, 'entities': len(seen), 'mapped_fields_checked': count,
          'scope': 'Field presence against independent catalog, not semantic completion', 'failures': failures}
(root / 'docs/quality/independent-qa/nine-migration-field-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
raise SystemExit(0 if report['passed'] else 1)
