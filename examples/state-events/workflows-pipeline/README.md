# Workflows 10 — Pipeline

A Workflow service wrapper for creating/checking workflow instances plus a D1-backed timeline route. The deterministic `/demo/start` path writes progress checkpoints to D1 so `/timeline/<id>` can be verified locally.

## Cloudflare docs

- [Workflows](https://developers.cloudflare.com/workflows/)

## Copy this API

```python
from xampler.workflows import WorkflowService

workflow = WorkflowService(env.PIPELINE)
started = await workflow.start()
status = await workflow.status(started.instance_id)
```
