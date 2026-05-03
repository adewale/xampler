# Workflows

## Import

```python
from xampler.workflows import WorkflowService
```

## Copy this API

```python
workflow = WorkflowService(env.PIPELINE)
started = await workflow.start()
status = await workflow.status(started.instance_id)
```

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
