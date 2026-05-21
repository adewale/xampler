# Durable Objects

## Import

```python
from xampler.durable_objects import DurableObjectNamespace, DurableObjectRef
```

## Copy this API

```python
namespace = DurableObjectNamespace(env.COUNTERS)
stub = namespace.named("global")
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Named Durable Object refs | Supported | Local examples verify named-object isolation. |
| HTTP fetch/text helpers | Supported | Thin wrapper over raw stubs. |
| Storage SQL, alarms, concurrency stress | Not covered | Product-specific examples still needed. |
| WebSocket hibernation | Caveated | Covered in chatroom example, with deeper remote coverage pending. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
