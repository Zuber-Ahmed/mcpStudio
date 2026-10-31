"""Read-only source checks; writes a report beside this script. No application tests."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'sources' / 'technical-documentation'
api = json.loads((src / 'specs/openapi.yaml').read_text(encoding='utf-8-sig'))
checks = []
def check(name, passed, detail=''):
    checks.append(dict(name=name, passed=bool(passed), detail=detail))

check('OpenAPI version', api.get('openapi') == '3.0.3')
ops = [(p, m, o) for p, methods in api['paths'].items() for m, o in methods.items()
       if m in {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}]
ids = [o['operationId'] for _, _, o in ops]
check('15 unique operation IDs', len(ids) == len(set(ids)) == 15)
check('23 component schemas', len(api['components']['schemas']) == 23)
check('global authentication declared', bool(api.get('security')))
refs = []
def walk(obj):
    if isinstance(obj, dict):
        if '$ref' in obj:
            refs.append(obj['$ref'])
        for v in obj.values():
            walk(v)
    elif isinstance(obj, list):
        for v in obj:
            walk(v)
walk(api)
for ref in sorted(set(refs)):
    target = api
    valid = ref.startswith('#/')
    try:
        if valid:
            for part in ref[2:].split('/'):
                target = target[part.replace('~1', '/').replace('~0', '~')]
    except (KeyError, TypeError):
        valid = False
    check('ref:' + ref, valid)
for path, method, op in ops:
    names = set(re.findall(r'\{([^}]+)\}', path))
    params = api['paths'][path].get('parameters', []) + op.get('parameters', [])
    declared = {p['name'] for p in params if p.get('in') == 'path' and p.get('required') is True}
    check('path parameters:' + op['operationId'], names == declared)
    check('success response:' + op['operationId'], any(str(k).startswith('2') for k in op['responses']))
erd = (src / 'specs/database-erd.mmd').read_text(encoding='utf-8')
entities = set(re.findall(r'^  ([A-Z_]+) \{', erd, re.M))
relations = re.findall(r'^  ([A-Z_]+) \|\|--o\{ ([A-Z_]+) : (.+)$', erd, re.M)
check('14 logical entities', len(entities) == 14)
check('18 relationships', len(relations) == 18)
check('relationship targets defined', all(a in entities and b in entities for a, b, _ in relations))
manifest_count = 0
for line in (src / 'quality/SHA256SUMS.txt').read_text().splitlines():
    if not line.strip():
        continue
    digest, relative = line.split(None, 1)
    path = (src / relative.strip()).resolve()
    valid_path = path.is_relative_to(src.resolve())
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if valid_path and path.is_file() else ''
    check('supplied manifest:' + relative.strip(), actual == digest.lower())
    manifest_count += 1
crosswalk = (root / 'technical-intake.md').read_text(encoding='utf-8')
for identifier in ids:
    check('operation mapped:' + identifier, identifier in crosswalk)
for entity in sorted(entities):
    check('entity mapped:' + entity, entity in crosswalk)
for n in range(1, 19):
    check('requirement mapped:R%02d' % n, bool(re.search(r'^\| R%02d \|' % n, crosswalk, re.M)))
for n in range(1, 6):
    check('screen mapped:S%d' % n, 'S%d' % n in crosswalk)
report = dict(scope='M0.1 structural draft inspection only', checks=checks,
              passed=all(c['passed'] for c in checks), check_count=len(checks),
              operation_count=len(ops), schema_count=len(api['components']['schemas']),
              entity_count=len(entities), relationship_count=len(relations),
              supplied_manifest_entries=manifest_count, runtime_tests_executed=0,
              full_openapi_semantic_validation=False, approved=False)
(root / 'technical-validation-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'checks'}))
if not report['passed']:
    print([c for c in checks if not c['passed']])
    raise SystemExit(1)
