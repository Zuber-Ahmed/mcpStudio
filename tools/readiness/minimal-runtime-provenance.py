"""Compare retained files to original package inventory without suppressing findings."""
from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('helpers',Path(__file__).with_name('evaluate-python-runtime-candidates.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
OUT=ROOT/'docs/quality/runtime-candidates/minimal-runtime'
PROBE=r'''
import json,pathlib
manifest=json.loads(pathlib.Path('/provenance/retained-files.json').read_text());by_path={r['path']:r for r in manifest}
def norm(s):
 if s.startswith('/lib/'):return '/usr/lib/'+s[5:]
 if s.startswith('/lib64/'):return '/usr/lib64/'+s[7:]
 return s
packages=[]
for file in pathlib.Path('/var/lib/dpkg/info').glob('*.list'):
 matches=[norm(p) for p in file.read_text().splitlines() if norm(p) in by_path]
 elf=[]
 for name in matches:
  p=pathlib.Path(name)
  if p.is_file():
   with p.open('rb') as f:
    if f.read(4)==b'\x7fELF':elf.append(name)
 packages.append({'package':file.name[:-5].split(':')[0],'retained_paths':matches,'retained_elf':elf})
print(json.dumps({'scope':'Original package ownership lists intersected with final retained-file manifest; original dpkg records intentionally include excluded payloads','packages':packages}))
'''
def main():
 a=json.loads((OUT/'assessment.json').read_text());assert a['complete']
 result=json.loads(h.container(a['image_id'],['python','-c',PROBE]))
 scan=json.loads((OUT/'scan.json').read_text());findings=[v for r in scan['Results'] for v in r.get('Vulnerabilities',[])]
 mapping={p['package']:p for p in result['packages']}
 result['scan_finding_rows']=len(findings);result['unmapped_scanner_packages']=sorted({v['PkgName'] for v in findings}-mapping.keys())
 assert not result['unmapped_scanner_packages']
 result['scanned_packages']=[{'package':name,'retained_paths':len(mapping[name]['retained_paths']),'retained_elf':mapping[name]['retained_elf']} for name in sorted({v['PkgName'] for v in findings})]
 result['waivers']=[];h.save(OUT/'package-provenance-coverage.json',result)
 print('All scanner-reported packages mapped to retained-file/original ownership evidence.')
if __name__=='__main__':main()
