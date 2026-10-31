from datetime import timedelta
from temporalio import workflow, activity
from temporalio.common import RetryPolicy

@activity.defn
def persist_fixture(payload: dict) -> dict:
    # Trusted fixture payload and local storage only, not an application adapter.
    from service_validation import storage_client
    import hashlib
    data=payload['body'].encode('utf-8')
    storage_client().put_object(Bucket=payload['bucket'],Key=payload['key'],Body=data,
        Metadata={'sha256':hashlib.sha256(data).hexdigest()})
    return {'key':payload['key'],'sha256':hashlib.sha256(data).hexdigest()}

@workflow.defn
class StoreReadinessWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        return await workflow.execute_activity(persist_fixture,payload,
            start_to_close_timeout=timedelta(seconds=20),retry_policy=RetryPolicy(maximum_attempts=2))
