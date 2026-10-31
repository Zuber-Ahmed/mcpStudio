"""Fresh minimal-image regressions and exclusion probe; no service restart or image adoption."""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import sys

root = Path(__file__).resolve().parents[3]
out = root / 'docs/quality/independent-qa/minimal-runtime'
out.mkdir(parents=True, exist_ok=True)
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
h = module('qa_helpers', root / 'tools/readiness/evaluate-python-runtime-candidates.py')
reviewer = module('qa_high_probe', root / 'tools/readiness/review-minimal-high-advisories.py')
assessment = json.loads((root / 'docs/quality/runtime-candidates/minimal-runtime/assessment.json').read_text())
image = assessment['image_id']
proof = json.loads(h.container(image, ['python', '-c', reviewer.PROBE]))
assert proof['manifest_hashes_verified'] and all(proof['checks'].values())
h.container(image, ['python', '/fixture/worker-readiness.py'], out)
h.run([sys.executable, '-X', 'utf8', root / 'tools/fixtures/m03/worker-boundary-runner.py', '--image', image, '--evidence-dir', out])
runtime = json.loads((out / 'worker-runtime-validation.json').read_text())
boundary = json.loads((out / 'worker-boundary-validation.json').read_text())
assert runtime['passed'] and boundary['passed'] and boundary['cleanup_complete']
scanpath = root / 'docs/quality/runtime-candidates/minimal-runtime/scan.json'
raw = json.loads(scanpath.read_text())
findings = [v for r in raw.get('Results', []) for v in r.get('Vulnerabilities', [])]
assert raw['Metadata']['OS']['Family'] == 'debian'
assert len(findings) == 164 and hashlib.sha256(scanpath.read_bytes()).hexdigest() == assessment['scan']['sha256']
restart = json.loads((root / 'docs/quality/runtime-candidates/minimal-restart/assessment.json').read_text())
assert restart['passed'] and restart['complete'] and restart['original_stack_before'] == restart['original_stack_after']
report = {'passed': True, 'image_id': image, 'fresh_runtime_boundary_entries': len(runtime['checks']) + len(boundary['checks']),
          'component_probe': proof, 'recorded_scan_counts': dict(collections.Counter(v['Severity'] for v in findings)),
          'restart_evidence_reviewed_not_rerun': True, 'adopted': False,
          'limits': 'Fresh runtime/isolation/retained-file checks; recorded restart evidence only. No new advisory or reachability assessment.'}
(out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
