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

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Start/status wrapper shape | Caveated | Local deterministic status is verified. |
| Real Workflow runtime status | Remote-only | Deeper deployed/runtime verification remains future work. |
| Typed event payloads and richer step inspection | Not covered | Future wrapper work. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
