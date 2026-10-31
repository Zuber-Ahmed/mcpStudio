"""Exact-image affected-component exclusion review; never rewrite raw scans."""
from pathlib import Path
import hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('helpers',Path(__file__).with_name('evaluate-python-runtime-candidates.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
OUT=ROOT/'docs/quality/runtime-candidates/minimal-restart'
PROBE=r'''
import hashlib,json,pathlib,shutil
manifest=json.loads(pathlib.Path('/provenance/retained-files.json').read_text())
for e in manifest:
 p=pathlib.Path(e['path'])
 if 'sha256' in e:assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],e['path']
paths=[e['path'] for e in manifest]
checks={n:shutil.which(n) is None for n in ['mount','umount','nsenter','infocmp','systemd-homed','homectl','perl']}
for name,pattern in [('libacl','libacl.so'),('libmount','libmount.so'),('Archive_Tar','/Archive/Tar.pm'),('systemd_homed_payload','systemd-homed')]:
 checks[name]=not any(pattern in p and not p.startswith(('/usr/share/doc/','/var/lib/dpkg/')) for p in paths)
assert all(checks.values())
print(json.dumps({'checks':checks,'manifest_hashes_verified':True,'manifest_entries':len(manifest),'scope':'Exact immutable image payload and PATH; historical dpkg/license records remain'}))
'''
def main():
 a=json.loads((ROOT/'docs/quality/runtime-candidates/minimal-runtime/assessment.json').read_text())
 image=a['image_id'];proof=json.loads(h.container(image,['python','-c',PROBE]));h.save(OUT/'component-exclusion-checks.json',proof)
 earlier=json.loads((ROOT/'docs/quality/runtime-candidates/python-path-review/high-advisory-review.json').read_text())
 coverage=json.loads((ROOT/'docs/quality/runtime-candidates/minimal-runtime/package-provenance-coverage.json').read_text())
 packages={p['package']:p for p in coverage['packages']}
 scanpath=ROOT/'docs/quality/runtime-candidates/minimal-runtime/scan.json';scan=json.loads(scanpath.read_text())
 highs=[v for r in scan['Results'] for v in r.get('Vulnerabilities',[]) if v['Severity']=='HIGH']
 conditions={
 'CVE-2026-76642':('Privileged mount helper/post-hook path',['mount','libmount1']),
 'CVE-2026-78408':('nsenter privileged cgroup-join path',['util-linux']),
 'CVE-2026-78409':('mount subdirectory path using libmount',['mount','libmount1']),
 'CVE-2026-78410':('Restricted bind mount path using libmount',['mount','libmount1']),
 'CVE-2026-54369':('libacl pathname functions',['libacl1']),
 'CVE-2025-69720':('infocmp analyze_string command path',['ncurses-bin']),
 'CVE-2026-16742':('systemd-homed managed-user path',['libsystemd0','libudev1']),
 'CVE-2026-9538':('Perl Archive::Tar parser',['perl-base'])}
 result=[]
 for old in earlier['review']:
  cid=old['id'];condition,relevant=conditions[cid]
  assert all(not packages[p]['retained_elf'] for p in relevant)
  result.append({'id':cid,'source':old['source'],'affected_component':condition,
    'scanner_occurrences':sum(v['VulnerabilityID']==cid for v in highs),
    'disposition':'Affected component excluded from this exact fixture candidate',
    'evidence':{'excluded_component_package_elf':{p:packages[p]['retained_elf'] for p in relevant},'runtime_probe':'component-exclusion-checks.json'},
    'limits':'Does not apply to baseline/server images, future payloads, additional mounts, plugins or replacement libraries. No raw scan suppression or risk acceptance.'})
 assert len(result)==8 and sum(r['scanner_occurrences'] for r in result)==44
 report={'image_id':image,'raw_scan_sha256':hashlib.sha256(scanpath.read_bytes()).hexdigest(),
 'review_complete_for_high_advisories':True,'review':result,'original_raw_findings':164,'other_severity_rows_still_need_semantic_review':120,
 'risk_acceptance':False,'suppression_file_created':False,'adopted':False,'h04_complete':False,
 'interpretation':'Scoped affected-component exclusion evidence; conservative original source-package records still produce 44 High entries. Not a globally clean image or an application-wide reachability proof.'}
 h.save(OUT/'high-advisory-dispositions.json',report)
 print('Eight High advisories have exact-candidate component-exclusion evidence; 120 other rows remain for semantic review.')
if __name__=='__main__':main()
