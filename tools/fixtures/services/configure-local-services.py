"""Local development services only. No production/source repository data."""
from pathlib import Path
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import urllib.request

root=Path(__file__).resolve().parents[3]
source=Path(__file__).resolve().parent
infra=root/'infra'
infra.mkdir(exist_ok=True)
local=root/'.local/services'
local.mkdir(parents=True,exist_ok=True)
fixture=root/'tools/fixtures/services'
fixture.mkdir(parents=True,exist_ok=True)
quality=root/'docs/quality'
secretfile=local/'credentials.json'
if secretfile.exists():
    credentials=json.loads(secretfile.read_text())
else:
    credentials={'db_password':secrets.token_urlsafe(32),'s3_key':'local-'+secrets.token_hex(12),'s3_secret':secrets.token_urlsafe(32)}
    secretfile.write_text(json.dumps(credentials),encoding='utf-8')
def sanitize(text):
    for value in credentials.values():text=text.replace(value,'[REDACTED]')
    return text
def run(args,timeout=300):
    p=subprocess.run([str(x) for x in args],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    if p.returncode:raise RuntimeError(sanitize(p.stdout+'\n'+p.stderr))
    return p.stdout.strip()
def digest(image):
    return json.loads(run(['docker','image','inspect',image,'--format','{{json .RepoDigests}}']))[0]
images=json.loads((root/'docs/quality/local-service-images.json').read_text())['images']
(local/'services.env').write_text('MCPSTUDIO_DB_PASSWORD='+credentials['db_password']+'\n',encoding='utf-8')
(local/'fixture.env').write_text('LOCAL_S3_ACCESS_KEY='+credentials['s3_key']+'\nLOCAL_S3_SECRET_KEY='+credentials['s3_secret']+'\nAWS_EC2_METADATA_DISABLED=true\n',encoding='utf-8')
sql={'pluginName':'postgres12','databaseName':'temporal','connectAddr':'postgres:5432',
     'connectProtocol':'tcp','user':'mcpstudio_local','password':credentials['db_password'],
     'maxConns':10,'maxIdleConns':5,'maxConnLifetime':'1h'}
visibility=dict(sql,databaseName='temporal_visibility')
config={'log':{'stdout':True,'level':'warn'},'persistence':{'defaultStore':'default','visibilityStore':'visibility',
    'numHistoryShards':4,'datastores':{'default':{'sql':sql},'visibility':{'sql':visibility}}},
    'global':{'membership':{'maxJoinDuration':'30s','broadcastAddress':'__CONTAINER_IP__'}},
    'services':{name:{'rpc':{'grpcPort':port,'membershipPort':member,'bindOnLocalHost':False}}
        for name,port,member in [('frontend',7233,6933),('history',7234,6934),('matching',7235,6935),('worker',7239,6939)]},
    'clusterMetadata':{'enableGlobalNamespace':False,'failoverVersionIncrement':10,'masterClusterName':'active',
        'currentClusterName':'active','clusterInformation':{'active':{'enabled':True,'initialFailoverVersion':1,
        'rpcName':'frontend','rpcAddress':'temporal:7233'}}},'dcRedirectionPolicy':{'policy':'noop'},
    'archival':{'history':{'state':'disabled','enableRead':False},'visibility':{'state':'disabled','enableRead':False}}}
(local/'temporal.yaml').write_text(json.dumps(config,indent=2),encoding='utf-8')
(local/'s3.json').write_text(json.dumps({'identities':[{'name':'mcpstudio-local-operator',
    'credentials':[{'accessKey':credentials['s3_key'],'secretKey':credentials['s3_secret']}],
    'actions':['Admin','Read','Write','List','Tagging']}]}),encoding='utf-8')
(infra/'temporal-databases.sql').write_text('CREATE DATABASE temporal;\nCREATE DATABASE temporal_visibility;\n',encoding='utf-8')
bootstrap='''#!/bin/sh
set -eu
for database in temporal temporal_visibility; do
  temporal-sql-tool --ep postgres --port 5432 --user mcpstudio_local --pw "$POSTGRES_PWD" --pl postgres12 --db "$database" setup-schema --version 0.0
  schema=temporal
  if [ "$database" = temporal_visibility ]; then schema=visibility; fi
  temporal-sql-tool --ep postgres --port 5432 --user mcpstudio_local --pw "$POSTGRES_PWD" --pl postgres12 --db "$database" update-schema --schema-dir "/etc/temporal/schema/postgresql/v12/$schema/versioned"
done
'''
(infra/'setup-temporal-schema.sh').write_text(bootstrap,encoding='utf-8',newline='\n')
launcher='''#!/bin/sh
set -eu
container_address=$(getent hosts "$(hostname)" | awk 'NR==1 {print $1}')
test -n "$container_address"
sed "s/__CONTAINER_IP__/$container_address/g" /run/temporal-template.yaml > /tmp/temporal.yaml
exec temporal-server --config-file /tmp/temporal.yaml --allow-no-auth start
'''
(infra/'run-temporal.sh').write_text(launcher,encoding='utf-8',newline='\n')
services={
 'postgres':{'image':images['postgres'],'environment':{'POSTGRES_USER':'mcpstudio_local','POSTGRES_DB':'postgres',
    'POSTGRES_PASSWORD':'${MCPSTUDIO_DB_PASSWORD:?local credentials required}'},
    'volumes':['postgres-data:/var/lib/postgresql/data','./temporal-databases.sql:/docker-entrypoint-initdb.d/01-temporal.sql:ro'],
    'healthcheck':{'test':['CMD-SHELL','pg_isready -U mcpstudio_local -d postgres'],'interval':'3s','timeout':'3s','retries':30},'mem_limit':'512m'},
 'schema':{'image':images['schema'],'entrypoint':['/bin/sh','/bootstrap.sh'],
    'environment':{'POSTGRES_PWD':'${MCPSTUDIO_DB_PASSWORD:?local credentials required}'},
    'volumes':['./setup-temporal-schema.sh:/bootstrap.sh:ro'],'depends_on':{'postgres':{'condition':'service_healthy'}}},
 'temporal':{'image':images['temporal'],'entrypoint':['/bin/sh','/run/start-temporal.sh'],
    'volumes':['../.local/services/temporal.yaml:/run/temporal-template.yaml:ro','./run-temporal.sh:/run/start-temporal.sh:ro'],
    'networks':['default','local-edge'],
    'ports':['127.0.0.1:7233:7233'],'depends_on':{'schema':{'condition':'service_completed_successfully'}},'mem_limit':'1g'},
 'storage':{'image':images['storage'],'command':['mini','-dir=/data','-ip=storage','-ip.bind=0.0.0.0',
    '-s3.config=/run/s3.json','-bucket=mcpstudio-fixtures','-master.telemetry=false','-admin.ui=false',
    '-webdav=false','-s3.port.iceberg=0','-s3.port.lance=0','-volume.max=4','-master.volumeSizeLimitMB=64'],
    'volumes':['storage-data:/data','../.local/services/s3.json:/run/s3.json:ro'],
    'ports':['127.0.0.1:8333:8333'],'networks':['default','local-edge'],'mem_limit':'512m'}
}
compose={'name':'mcpstudio-local','services':services,'volumes':{'postgres-data':{},'storage-data':{}},'networks':{'default':{'internal':True},'local-edge':{'driver':'bridge'}}}
(infra/'compose.yaml').write_text(json.dumps(compose,indent=2)+'\n',encoding='utf-8')
print('Local configuration generated; credentials retained under ignored .local/services.')
