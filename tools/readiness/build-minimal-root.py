"""Runs only in a trusted image build stage. Assemble an explicit candidate root."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess
out=Path('/candidate-root');out.mkdir()
def normalized(path):
 s=str(path)
 for old,new in [('/lib64/','/usr/lib64/'),('/lib/','/usr/lib/')]:
  if s.startswith(old):return new+s[len(old):]
 return s
def copy(path):
 p=Path(path);target=out/normalized(p).lstrip('/')
 target.parent.mkdir(parents=True,exist_ok=True)
 if p.is_dir():shutil.copytree(p,target,dirs_exist_ok=True,symlinks=True)
 else:shutil.copy2(p,target,follow_symlinks=True)
for name in ['/usr/local/lib','/fixture','/usr/share/zoneinfo','/usr/share/doc','/usr/lib/locale','/etc/ssl','/usr/lib/ssl','/usr/share/ca-certificates']:
 if Path(name).exists():copy(name)
for pattern in ['tkinter','idlelib','lib-dynload/_tkinter*','config-*']:
 for p in (out/'usr/local/lib/python3.14').glob(pattern):
  if p.is_dir():shutil.rmtree(p)
  else:p.unlink()
copy('/usr/local/bin/python3.14')
for name in ['python','python3']:(out/'usr/local/bin'/name).symlink_to('python3.14')
for path in ['/etc/debian_version','/etc/passwd','/etc/group','/etc/nsswitch.conf','/etc/gai.conf','/etc/localtime','/etc/timezone','/etc/os-release','/usr/lib/os-release']:
 if Path(path).exists():copy(path)
for path in ['/usr/lib/x86_64-linux-gnu/gconv','/etc/ld.so.cache','/etc/ld.so.conf','/etc/ld.so.conf.d']:
 if Path(path).exists():copy(path)
# Keep original package records as conservative scanner/provenance input, even
# where administrative payloads are excluded. Never present them as an installable dpkg database.
copy('/var/lib/dpkg/status');copy('/var/lib/dpkg/info')
targets=[]
for p in (out/'usr/local').rglob('*'):
 if p.is_file() and not p.is_symlink():
  with p.open('rb') as f:
   if f.read(4)==b'\x7fELF':targets.append('/'+str(p.relative_to(out)))
deps=set();checks=[]
for path in targets:
 p=subprocess.run(['ldd',path],capture_output=True,text=True,timeout=30)
 assert p.returncode==0 and 'not found' not in p.stdout,(path,p.stdout,p.stderr)
 checks.append({'path':path,'ldd':p.stdout})
 deps.update(re.findall(r'(/[^\s()]+)',p.stdout))
# NSS and OpenSSL may load plugins dynamically rather than via DT_NEEDED.
deps.update(str(p) for p in Path('/usr/lib/x86_64-linux-gnu').glob('libnss_*.so*'))
for path in sorted(deps):
 if not path.startswith('/usr/local/'):copy(path)
provider=Path('/usr/lib/x86_64-linux-gnu/ossl-modules')
if provider.exists():copy(provider)
for name in ['tmp','usr/bin','usr/sbin','usr/lib64','proc','dev','evidence']:(out/name).mkdir(parents=True,exist_ok=True)
(out/'tmp').chmod(0o1777)
for name,target in [('lib','usr/lib'),('lib64','usr/lib64'),('bin','usr/bin'),('sbin','usr/sbin')]:
 (out/name).symlink_to(target)
inventory=[]
for p in sorted(out.rglob('*')):
 if p.is_symlink():inventory.append({'path':'/'+str(p.relative_to(out)),'symlink':os.readlink(p)})
 elif p.is_file():
  p.chmod(p.stat().st_mode & ~0o6000)
  inventory.append({'path':'/'+str(p.relative_to(out)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
proof=out/'provenance';proof.mkdir()
(proof/'retained-files.json').write_text(json.dumps(inventory,indent=2))
(proof/'native-build-checks.json').write_text(json.dumps(checks,indent=2))
(proof/'scope.json').write_text(json.dumps({'dpkg_inventory':'Original input inventory retained conservatively; not a description of fully installed package payloads','excluded_support':['GUI/Tkinter/IDLE','shell commands','package installation','administrative utilities'],'adopted':False}))
