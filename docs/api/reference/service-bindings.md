# Service Bindings

## Import

```python
from xampler.service_bindings import ServiceBinding
```

## Copy this API

```python
service = ServiceBinding(env.PY_PROVIDER)
result = await service.call("highlight_code", "print(1)")
```

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
