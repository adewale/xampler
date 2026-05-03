# Workflows 10 — Pipeline

A Workflow service wrapper for creating and checking workflow instances.

## Cloudflare docs

- [Workflows](https://developers.cloudflare.com/workflows/)

## Copy this API

```python
from xampler.workflows import WorkflowService

workflow = WorkflowService(env.PIPELINE)
started = await workflow.start()
status = await workflow.status(started.instance_id)
```
