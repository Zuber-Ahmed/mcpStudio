"""Build/test one isolated minimal service/worker fixture; never adopt or restart services."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil,subprocess,sys
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
ROOT=Path(__file__).resolve().parents[2]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('helpers','evaluate-python-runtime-candidates.py');osreview=module('osreview','evaluate-python-os-candidates.py')
OUT=ROOT/'docs/quality/runtime-candidates/minimal-runtime';WORK=ROOT/'work/runtime-candidates/minimal-runtime'
def main():
 OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
 baseline=json.loads((ROOT/'docs/quality/runtime-candidates/python-tooling-free/assessment.json').read_text())
 prior=next(x for x in baseline['images'] if x['label']=='service_fixture');info=h.inspect(prior['candidate_id']);assert info['Id']==prior['candidate_id']
 database=json.loads((ROOT/'work/runtime-audit/cache/db/metadata.json').read_text());assert database==baseline['database_metadata']
 report={'complete':False,'adopted':False,'h04_complete':False,'input_id':info['Id'],'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'database_metadata':database}
 h.save(OUT/'assessment.json',report)
 alias='mcpstudio-minimal-input:'+info['Id'].split(':')[1];h.run(['docker','tag',info['Id'],alias])
 shutil.copyfile(Path(__file__).with_name('build-minimal-root.py'),WORK/'build-minimal-root.py')
 recipe=f'FROM {alias} AS assembler\nUSER root\nCOPY build-minimal-root.py /tmp/build-minimal-root.py\nRUN python /tmp/build-minimal-root.py\nFROM scratch\nCOPY --from=assembler /candidate-root /\n'
 for env in info['Config']['Env']:
  k,v=env.split('=',1);recipe+=f'ENV {k}={json.dumps(v)}\n'
 recipe+='WORKDIR /fixture\nUSER 65534:65534\nCMD ["python", "/fixture/service_validation.py"]\n'
 (WORK/'Dockerfile').write_text(recipe);(OUT/'Dockerfile').write_text(recipe)
 print('Building isolated minimal runtime.',flush=True)
 p=subprocess.run(['docker','build','--network=none','--pull=false','--progress=plain','-t','mcpstudio-minimal-runtime:candidate',str(WORK)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=500)
 (OUT/'build.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');assert p.returncode==0,p.stderr[-3000:]
 candidate=h.inspect('mcpstudio-minimal-runtime:candidate');image=candidate['Id'];report['image_id']=image
 for name in ['retained-files.json','native-build-checks.json','scope.json']:
  value=json.loads(h.container(image,['python','-c',f'import pathlib;print(pathlib.Path("/provenance/{name}").read_text())']));h.save(OUT/name,value)
 inv=json.loads(h.container(image,['python','-c',h.INVENTORY]));assert inv==prior['inventory_after'];report['inventory']=inv
 key=rsa.generate_private_key(public_exponent=65537,key_size=2048);now=datetime.datetime.now(datetime.timezone.utc)
 subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'MCPStudio disposable TLS fixture')])
 cert=(x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number())
       .not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=1))
       .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]),critical=False)
       .add_extension(x509.BasicConstraints(ca=True,path_length=None),critical=True).sign(key,hashes.SHA256()))
 tls={'cert':cert.public_bytes(serialization.Encoding.PEM).decode(),'key':key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode()}
 probe=Path(__file__).with_name('check-minimal-runtime.py').read_text()
 checks=json.loads(h.container(image,['python','-c',probe,json.dumps(tls)]));assert checks['passed'];h.save(OUT/'minimal-runtime-validation.json',checks)
 print('Checking parser, isolation and local workflow/storage integration.',flush=True)
 h.container(image,['python','/fixture/worker-readiness.py'],OUT)
 h.run([sys.executable,'-X','utf8',ROOT/'tools/fixtures/m03/worker-boundary-runner.py','--image',image,'--evidence-dir',OUT])
 env=ROOT/'.local/services/fixture.env'
 dns=json.loads(h.container(image,['python','-c','import socket,json;print(json.dumps({n:bool(socket.getaddrinfo(n,p)) for n,p in [("temporal",7233),("storage",8333)]}))'],network='mcpstudio-local_default'))
 assert all(dns.values());h.save(OUT/'service-dns-validation.json',dns)
 h.container(image,['python','/fixture/service_validation.py'],OUT,'mcpstudio-local_default',env)
 h.container(image,['python','-c',h.CLEANUP],OUT,'mcpstudio-local_default',env)
 for name in ['worker-runtime-validation.json','worker-boundary-validation.json','local-service-validation.json']:
  r=json.loads((OUT/name).read_text());assert r['passed'];report[name]=len(r['checks'])
 print('Scanning exact minimal image with original package provenance retained.',flush=True)
 report['scan']=osreview.scan(image,OUT/'scan.json');report['baseline_scan_counts']=prior['candidate_counts']
 assert report['scan']['os']['Family']=='debian', 'OS scan coverage failed; not a clean result'
 report['minimal_checks']=len(checks['checks']);report['dns_checks']=len(dns)
 report['complete']=True;h.save(OUT/'assessment.json',report)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
