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

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
