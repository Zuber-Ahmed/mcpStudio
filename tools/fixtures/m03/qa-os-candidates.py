"""Independent candidate runtime/boundary rerun and raw scan reconciliation; no adoption."""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import sys

root = Path(__file__).resolve().parents[3]
out = root / 'docs/quality/independent-qa/os-candidates'
out.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('candidate_helpers', root / 'tools/readiness/evaluate-python-runtime-candidates.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
assessment = json.loads((root / 'docs/quality/runtime-candidates/python-os/assessment.json').read_text())
report = {'scope': 'Fresh runtime/boundary tests and reconciliation of recorded unsuppressed scan evidence; no new advisory scan',
          'candidates': [], 'adopted': False}
original = h.inspect('mcpstudio-worker-readiness:0.1.0')['Id']
for candidate in assessment['candidates']:
    label = candidate['label']
    image = candidate['image_id']
    assert h.inspect(image)['Id'] == image
    evidence = out / label
    evidence.mkdir(exist_ok=True)
    inventory = json.loads(h.container(image, ['python', '-c', h.INVENTORY]))
    assert inventory == candidate['inventory']
    h.container(image, ['python', '/fixture/worker-readiness.py'], evidence)
    h.run([sys.executable, '-X', 'utf8', root / 'tools/fixtures/m03/worker-boundary-runner.py',
           '--image', image, '--evidence-dir', evidence])
    runtime = json.loads((evidence / 'worker-runtime-validation.json').read_text())
    boundary = json.loads((evidence / 'worker-boundary-validation.json').read_text())
    assert runtime['passed'] and boundary['passed'] and boundary['cleanup_complete']
    scan_path = root / 'docs/quality/runtime-candidates/python-os' / (label + '-scan.json')
    raw = json.loads(scan_path.read_text())
    findings = [v for r in raw.get('Results', []) for v in r.get('Vulnerabilities', [])]
    counts = dict(collections.Counter(v['Severity'] for v in findings))
    assert counts == candidate['scan']['counts'] and len(findings) == candidate['scan']['findings']
    assert hashlib.sha256(scan_path.read_bytes()).hexdigest() == candidate['scan']['sha256']
    report['candidates'].append({'label': label, 'image_id': image, 'runtime_checks': len(runtime['checks']),
                                'boundary_checks': len(boundary['checks']), 'recorded_scan_counts': counts,
                                'recorded_scan_entries': len(findings), 'scan_hash_matches': True})
assert h.inspect('mcpstudio-worker-readiness:0.1.0')['Id'] == original
report['approved_worker_tag_unchanged'] = True
report['fresh_check_entries'] = sum(c['runtime_checks'] + c['boundary_checks'] for c in report['candidates'])
report['passed'] = True
(out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
