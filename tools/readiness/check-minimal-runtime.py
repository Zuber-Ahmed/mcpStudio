"""Trusted local candidate tests; no application sources or public network."""
import ctypes,importlib.util,json,locale,os,pathlib,pwd,shutil,socket,ssl,stat,sys,threading
from zoneinfo import ZoneInfo
checks=[]
def check(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
check('prohibited commands absent',all(shutil.which(n) is None for n in ['sh','bash','dash','apt','apt-get','dpkg','perl','mount','umount','nsenter','su','sudo','infocmp','passwd']))
check('pip and GUI modules explicitly absent',all(importlib.util.find_spec(n) is None for n in ['pip','ensurepip','tkinter','idlelib','_tkinter']))
check('non-root NSS identity resolves',pwd.getpwuid(os.getuid()).pw_uid==65534)
check('UTF-8 locale available','UTF-8' in locale.setlocale(locale.LC_ALL,'C.UTF-8').upper())
check('timezone data available',ZoneInfo('Asia/Kolkata').key=='Asia/Kolkata')
check('hosts resolution works',bool(socket.getaddrinfo('localhost',443)))
check('system CA trust retained',ssl.create_default_context().cert_store_stats()['x509_ca']>0)
manifest=json.loads(pathlib.Path('/provenance/retained-files.json').read_text());native=0;setid=[]
import hashlib
for entry in manifest:
 p=pathlib.Path(entry['path'])
 if 'sha256' in entry:
  assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],entry['path']
  if p.stat().st_mode & 0o6000:setid.append(entry['path'])
  if '/usr/local/lib/' in str(p) and '.so' in p.name:
   with p.open('rb') as f:magic=f.read(4)
   if magic==b'\x7fELF':ctypes.CDLL(str(p));native+=1
check('retained file hashes match manifest',True)
check('no retained set-ID files',not setid)
check('retained Python native libraries load',native>70)
# Controlled loopback TLS: one explicitly trusted connection and two rejection tests.
data=json.loads(sys.argv[1]);cert=pathlib.Path('/tmp/fixture-ca.pem');key=pathlib.Path('/tmp/fixture-key.pem')
cert.write_text(data['cert']);key.write_text(data['key']);server=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server.load_cert_chain(cert,key)
listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(3);listener.settimeout(10);port=listener.getsockname()[1];errors=[]
def serve():
 try:
  for _ in range(3):
   connection,_=listener.accept()
   try:
    with server.wrap_socket(connection,server_side=True) as s:s.sendall(b'ok')
   except ssl.SSLError:connection.close()
 except Exception as e:errors.append(str(e))
 finally:listener.close()
t=threading.Thread(target=serve);t.start()
trusted=ssl.create_default_context(cafile=str(cert))
with trusted.wrap_socket(socket.create_connection(('127.0.0.1',port),timeout=5),server_hostname='localhost') as s:check('TLS trusted local certificate succeeds',s.recv(2)==b'ok')
for name,context,hostname in [('TLS hostname mismatch rejected',trusted,'wrong.invalid'),('TLS untrusted issuer rejected',ssl.create_default_context(),'localhost')]:
 try:
  with context.wrap_socket(socket.create_connection(('127.0.0.1',port),timeout=5),server_hostname=hostname):check(name,False)
 except ssl.SSLCertVerificationError:check(name,True)
t.join(12);check('TLS fixture terminates cleanly',not t.is_alive() and not errors);cert.unlink();key.unlink()
print(json.dumps({'passed':all(c['passed'] for c in checks),'checks':checks,'native_libraries_loaded':native,'retained_file_entries':len(manifest),'scope':'Explicit minimal candidate support boundary, not all Python stdlib/plugin compatibility'}))
