from pathlib import Path
import hashlib,json,urllib.request,zipfile,subprocess,datetime
root=Path(__file__).resolve().parents[2];work=root/'work/runtime-audit';work.mkdir(parents=True,exist_ok=True)
q=root/'docs/quality/runtime-audit';q.mkdir(parents=True,exist_ok=True)
version='0.76.1';asset=f'trivy_{version}_windows-64bit.zip';base=f'https://github.com/aquasecurity/trivy/releases/download/v{version}/'
archive=work/asset;checksum=work/f'trivy_{version}_checksums.txt'
for name,target in [(asset,archive),(checksum.name,checksum)]:
 if not target.exists():
  print('Downloading official scanner asset: '+name,flush=True)
  urllib.request.urlretrieve(base+name,target)
expected=next(line.split()[0] for line in checksum.read_text().splitlines() if line.split()[-1].lstrip('*')==asset)
actual=hashlib.sha256(archive.read_bytes()).hexdigest()
assert expected==actual,'Official checksum mismatch'
with zipfile.ZipFile(archive) as z:
 name=next(n for n in z.namelist() if n=='trivy.exe')
 (work/'trivy.exe').write_bytes(z.read(name))
result=subprocess.run([str(work/'trivy.exe'),'--version'],capture_output=True,text=True,check=True)
record={'recorded_date':'2026-10-30','version':version,'source':base+asset,'official_checksum_source':base+checksum.name,
 'archive_sha256':actual,'binary_sha256':hashlib.sha256((work/'trivy.exe').read_bytes()).hexdigest(),'checksum_verified':True,
 'signature_verified':False,'installed_path':'work/runtime-audit/trivy.exe','global_installation':False,'version_output':result.stdout.strip(),
 'scout_probe':{'version':'1.27.0','scan_complete':False,'reason':'Docker Hub authentication required; local-first account-free scanner selected'}}
(q/'scanner-provenance.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('Official scanner checksum verified; '+result.stdout.strip(),flush=True)
