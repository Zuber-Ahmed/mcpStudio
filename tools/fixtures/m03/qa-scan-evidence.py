"""Recount recorded scanner reports without querying new advisory data."""
from pathlib import Path
import collections
import hashlib
import json

root = Path(__file__).resolve().parents[3]
review = json.loads((root / 'docs/quality/runtime-audit/image-review.json').read_text())
results = []
for image in review['images']:
    path = root / image['report_path']
    raw = json.loads(path.read_text(encoding='utf-8'))
    findings = [v for r in raw.get('Results', []) for v in r.get('Vulnerabilities', [])]
    counts = dict(collections.Counter(v['Severity'] for v in findings))
    assert counts == image['severity_counts']
    assert len(findings) == image['findings_count']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == image['report_sha256']
    results.append({'image': image['label'], 'entries': len(findings), 'counts': counts, 'hash_matches': True})
for label in ['worker_fixture', 'service_fixture']:
    path = root / ('docs/quality/runtime-candidates/python-tooling-free/' + label + '-scan.json')
    raw = json.loads(path.read_text())
    findings = [v for r in raw.get('Results', []) for v in r.get('Vulnerabilities', [])]
    library = [v for r in raw.get('Results', []) if r.get('Class') == 'lang-pkgs' for v in r.get('Vulnerabilities', [])]
    assert len(findings) == 164 and not library
    results.append({'image': label + '_tooling_free', 'entries': len(findings), 'library_findings': len(library)})
report = {'scope': 'Recorded scan counts and baseline report hashes; not a fresh vulnerability scan or reachability analysis',
          'passed': True, 'reports': results}
(root / 'docs/quality/independent-qa/scan-evidence-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
