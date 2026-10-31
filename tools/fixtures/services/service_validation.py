import asyncio
import hashlib
import json
import os
from pathlib import Path
from datetime import timedelta
import uuid
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.api.workflowservice.v1 import RegisterNamespaceRequest
from temporalio.service import RPCError, RPCStatusCode
from google.protobuf.duration_pb2 import Duration

def storage_client(bad=False):
    return boto3.client('s3',endpoint_url='http://storage:8333',region_name='us-east-1',
        aws_access_key_id=os.environ['LOCAL_S3_ACCESS_KEY'],
        aws_secret_access_key=('incorrect-fixture-secret' if bad else os.environ['LOCAL_S3_SECRET_KEY']),
        config=Config(signature_version='s3v4',s3={'addressing_style':'path'},
                      connect_timeout=3,read_timeout=10,retries={'max_attempts':2}))

async def connect():
    last=None
    for _ in range(45):
        try:
            c=await Client.connect('temporal:7233',namespace='mcpstudio-local')
            if not await c.service_client.check_health():
                raise RuntimeError('Temporal reported not-serving health')
            return c
        except Exception as ex:
            last=ex
            await asyncio.sleep(2)
    raise RuntimeError('Temporal readiness timeout: '+str(last))

async def wait_storage(client):
    for attempt in range(45):
        try:
            client.head_bucket(Bucket='mcpstudio-fixtures')
            return
        except Exception:
            if attempt==44:raise
            await asyncio.sleep(2)

async def main():
    from service_workflow import StoreReadinessWorkflow,persist_fixture
    mode=os.environ.get('FIXTURE_PHASE','initial')
    evidence=Path('/evidence/local-service-validation.json')
    checks=[]
    def check(name,ok):checks.append({'name':name,'passed':bool(ok)})
    client=await connect()
    check('Temporal gRPC health',True)
    if mode=='initial':
        try:
            await client.workflow_service.register_namespace(RegisterNamespaceRequest(
                namespace='mcpstudio-local',workflow_execution_retention_period=Duration(seconds=86400)))
        except RPCError as ex:
            if ex.status!=RPCStatusCode.ALREADY_EXISTS:raise
        check('dedicated local namespace available',True)
        s3=storage_client()
        await wait_storage(s3)
        check('authenticated local S3 bucket access',True)
        try:
            storage_client(bad=True).list_objects_v2(Bucket='mcpstudio-fixtures',MaxKeys=1)
            check('incorrect storage credentials denied',False)
        except ClientError as ex:
            check('incorrect storage credentials denied',ex.response['ResponseMetadata']['HTTPStatusCode'] in [401,403])
        token=uuid.uuid4().hex
        workflow_id='m03-storage-'+token
        key='readiness/'+token+'.txt'
        body='MCPStudio local service fixture '+token
        queue='m03-readiness-'+token
        with ThreadPoolExecutor(max_workers=2) as executor:
            async with Worker(client,task_queue=queue,workflows=[StoreReadinessWorkflow],activities=[persist_fixture],activity_executor=executor):
                result=await client.execute_workflow(StoreReadinessWorkflow.run,
                    {'bucket':'mcpstudio-fixtures','key':key,'body':body},id=workflow_id,task_queue=queue,
                    execution_timeout=timedelta(seconds=60))
        expected=hashlib.sha256(body.encode()).hexdigest()
        check('Temporal workflow executes storage activity',result=={'key':key,'sha256':expected})
        obj=s3.get_object(Bucket='mcpstudio-fixtures',Key=key)
        data=obj['Body'].read()
        check('S3 upload download bytes match',data.decode()==body)
        check('artifact digest and metadata match',hashlib.sha256(data).hexdigest()==expected==obj['Metadata']['sha256'])
        state={'workflow_id':workflow_id,'key':key,'sha256':expected,'namespace':'mcpstudio-local'}
        report={'scope':'Local Temporal/PostgreSQL/SeaweedFS readiness with trusted fixture data only',
                'passed':all(x['passed'] for x in checks),'checks':checks,'fixture':state,
                'restart_phase_complete':False,'fixture_object_removed':False}
    else:
        report=json.loads(evidence.read_text())
        state=report['fixture']
        result=await client.get_workflow_handle(state['workflow_id']).result()
        check('completed workflow result survives service restart',result['sha256']==state['sha256'])
        s3=storage_client()
        await wait_storage(s3)
        data=s3.get_object(Bucket='mcpstudio-fixtures',Key=state['key'])['Body'].read()
        check('stored object survives storage restart',hashlib.sha256(data).hexdigest()==state['sha256'])
        # Only remove this invocation's unique fixture object, never a bucket or other keys.
        s3.delete_object(Bucket='mcpstudio-fixtures',Key=state['key'])
        try:
            s3.head_object(Bucket='mcpstudio-fixtures',Key=state['key'])
            check('unique fixture object cleanup',False)
        except ClientError as ex:
            check('unique fixture object cleanup',ex.response['ResponseMetadata']['HTTPStatusCode']==404)
        report['checks']+=checks
        report['restart_phase_complete']=True
        report['fixture_object_removed']=checks[-1]['passed']
        report['passed']=all(x['passed'] for x in report['checks'])
    evidence.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':asyncio.run(main())
