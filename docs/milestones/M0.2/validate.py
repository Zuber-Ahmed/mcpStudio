"""Documentation consistency, source integrity and coverage; no runtime tests."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
checks = []
def check(name, ok):
    checks.append({'name': name, 'passed': bool(ok)})
names = ['README.md', 'baseline.md', 'decisions.md', 'contract-amendment.md',
         'reconciliation.md', 'acceptance-and-tracker.md']
texts = {}
for name in names:
    p = root / name
    check('artifact:' + name, p.is_file())
    texts[name] = p.read_text(encoding='utf-8')
for name, text in texts.items():
    for link in re.findall(r'\]\(([^)]+)\)', text):
        if link == 'validation-results.json':
            continue  # Produced after these checks, not an input artifact.
        if not re.match(r'\w+://', link):
            check('local link:' + name + ':' + link, (root / link).is_file())
    for row in text.splitlines():
        if row.startswith('|'):
            check('table closed:' + name, row.endswith('|'))
for prefix, count, width in [('PC', 7, 2), ('TC', 8, 2), ('G', 15, 2)]:
    for n in range(1, count + 1):
        key = prefix + str(n).zfill(width)
        check('source disposition:' + key,
              bool(re.search(r'^\| ' + key + r' \|', texts['reconciliation.md'], re.M)))
for prefix, count, name in [('BL', 14, 'baseline.md'), ('CA', 8, 'contract-amendment.md'),
                            ('M02-D', 12, 'decisions.md'), ('AC', 10, 'acceptance-and-tracker.md')]:
    for n in range(1, count + 1):
        check('defined:' + prefix + str(n).zfill(2), prefix + str(n).zfill(2) in texts[name])
for text in texts.values():
    for prefix, n in re.findall(r'\b(BL|CA|M02-D|AC)(\d{2})\b', text):
        target = {'BL': 'baseline.md', 'CA': 'contract-amendment.md',
                  'M02-D': 'decisions.md', 'AC': 'acceptance-and-tracker.md'}[prefix]
        check('reference:' + prefix + n, prefix + n in texts[target])
source_check = subprocess.run([sys.executable, str(root.parent / 'M0.1/validate-technical.py')],
                              capture_output=True, text=True)
check('M0.1 archived technical integrity', source_check.returncode == 0)
manifest = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}
report = {'scope': 'M0.2 documentation consistency only', 'passed': all(x['passed'] for x in checks),
          'check_count': len(checks), 'failed': [x for x in checks if not x['passed']],
          'source_integrity_output': source_check.stdout.strip(), 'document_sha256': manifest,
          'runtime_tests_executed': 0, 'application_code_created': False,
          'replacement_openapi_or_migrations_created': False, 'user_baseline_approval': 'pending'}
(root / 'validation-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['passed'] else 1)
