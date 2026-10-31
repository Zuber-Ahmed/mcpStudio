"""Collect bounded runtime-path evidence; no vulnerability waiver or package removal."""
from pathlib import Path
import collections, hashlib, importlib.util, json
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('helpers',Path(__file__).with_name('evaluate-python-runtime-candidates.py'))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
OUT=ROOT/'docs/quality/runtime-candidates/python-path-review'
PROBE=r'''
import contextlib,hashlib,io,json,os,pathlib,runpy,shutil,stat,subprocess,sys
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=30)
 return {'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
packages=json.loads(sys.argv[1]);report={}
report['status']={k:v.strip() for k,v in (line.split(':',1) for line in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in line) if k in ['Uid','Gid','CapEff','CapPrm','CapBnd','NoNewPrivs','Seccomp']}
report['package_inventory']=run(['dpkg-query','-W','-f=${binary:Package}\t${Version}\t${source:Package}\n'])
report['package_files']={}
for package in packages:
 result=run(['dpkg-query','-L',package]); assert result['exit_code']==0
 files=[]
 for name in result['stdout'].splitlines():
  p=pathlib.Path(name)
  if not p.is_file():continue
  s=p.stat();record={'path':name,'resolved':str(p.resolve()),'bytes':s.st_size,'mode':oct(stat.S_IMODE(s.st_mode))}
  with p.open('rb') as f:magic=f.read(4)
  record['elf']=magic==b'\x7fELF'
  record['setid']=bool(s.st_mode & (stat.S_ISUID|stat.S_ISGID))
  if record['elf'] or record['setid']:record['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
  files.append(record)
 report['package_files'][package]=files
report['commands']={name:shutil.which(name) for name in ['mount','umount','nsenter','infocmp','perl','systemd-homed','homectl','sh','bash','apt','dpkg']}
report['homed_paths']={p:pathlib.Path(p).exists() for p in ['/usr/lib/systemd/systemd-homed','/lib/systemd/systemd-homed','/usr/bin/homectl']}
report['perl_archive_tar']=run(['perl','-MArchive::Tar','-e','print $Archive::Tar::VERSION'])
report['fstab']=pathlib.Path('/etc/fstab').read_text()
capture=io.StringIO()
with contextlib.redirect_stdout(capture):runpy.run_path('/fixture/worker-readiness.py',run_name='__main__')
report['fixture_report']=json.loads(pathlib.Path('/evidence/worker-runtime-validation.json').read_text())
report['fixture_module_files']=sorted({str(pathlib.Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and pathlib.Path(m.__file__).is_file()})
report['mapped_files_after_fixture']=sorted({line.split()[-1] for line in pathlib.Path('/proc/self/maps').read_text().splitlines() if len(line.split())>=6 and line.split()[-1].startswith('/')})
targets={pathlib.Path('/usr/local/bin/python3.14'),*pathlib.Path('/usr/local/lib').rglob('*.so'),*pathlib.Path('/usr/local/lib').glob('*.so.*')}
report['native_dependency_checks']=[]
for p in sorted(targets):
 if not p.is_file():continue
 with p.open('rb') as f:magic=f.read(4)
 if magic!=b'\x7fELF':continue
 result=run(['ldd',str(p)]);result['path']=str(p);report['native_dependency_checks'].append(result)
report['scope']='Observed fixture imports/maps plus ldd on trusted Python/native modules. Not all-path reachability or hostile-source execution.'
print(json.dumps(report))
'''
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=ROOT/'docs/quality/runtime-candidates/python-tooling-free/worker_fixture-scan.json'
 prior=json.loads((ROOT/'docs/quality/runtime-candidates/python-tooling-free/assessment.json').read_text())
 entry=next(e for e in prior['images'] if e['label']=='worker_fixture');image=entry['candidate_id']
 assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['scan_sha256']
 raw=json.loads(source.read_text(encoding='utf-8'));findings=[v for r in raw['Results'] for v in r.get('Vulnerabilities',[])]
 packages=sorted({v['PkgName'] for v in findings})
 print('Collecting package ownership, native dependency and fixture execution evidence.',flush=True)
 probe=json.loads(h.container(image,['python','-c',PROBE,json.dumps(packages)],OUT))
 h.save(OUT/'runtime-path-evidence.json',probe)
 assert probe['fixture_report']['passed'] and probe['status']['CapEff']=='0000000000000000' and probe['status']['NoNewPrivs']=='1'
 unresolved=[r['path'] for r in probe['native_dependency_checks'] if r['exit_code']!=0 or 'not found' in r['stdout']]
 sources={}
 for line in probe['package_inventory']['stdout'].splitlines():
  name,version,src=line.split('\t');sources[name.split(':')[0]]={'version':version,'source':src}
 mapped=set(probe['mapped_files_after_fixture']);matrix=[]
 for v in findings:
  pkg=v['PkgName'];files=probe['package_files'][pkg]
  matrix.append({'id':v['VulnerabilityID'],'severity':v['Severity'],'package':pkg,'installed':v['InstalledVersion'],
   'source_package':sources[pkg]['source'],'package_inventory_version':sources[pkg]['version'],
   'present_regular_files':len(files),'elf_files':[f['path'] for f in files if f['elf']],
   'observed_mapped_files':[f['path'] for f in files if f['resolved'] in mapped],
   'review_status':'OPEN: source/package presence is not affected-code reachability',
   'source_url':'https://security-tracker.debian.org/tracker/'+v['VulnerabilityID']})
 h.save(OUT/'finding-path-matrix.json',{'image_id':image,'scan_sha256':entry['scan_sha256'],'rows':matrix})
 groups={}
 for r in matrix:
  if r['severity']=='HIGH':groups.setdefault(r['id'],[]).append(r['package'])
 result={'complete':True,'image_id':image,'finding_rows':len(matrix),'packages':len(packages),'high_occurrences':sum(len(v) for v in groups.values()),
  'unique_high_advisories':len(groups),'high_groups':groups,'fixture_checks':len(probe['fixture_report']['checks']),
  'native_dependency_checks':len(probe['native_dependency_checks']),'all_native_dependencies_resolved':not unresolved,'unresolved_native_modules':unresolved,
  'h04_complete':False,'adopted':False,'waivers':[]}
 h.save(OUT/'assessment.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
