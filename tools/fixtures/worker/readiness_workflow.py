from temporalio import workflow

@workflow.defn
class ReadinessWorkflow:
    @workflow.run
    async def run(self, label: str) -> str:
        return 'fixture:' + label
