# Service Bindings

Experimental surface: currently a small RPC-shaped helper and demo binding, not the final Service Bindings API.

## Import

```python
from xampler.experimental.service_bindings import ServiceBinding
```

## Copy this API

```python
service = ServiceBinding(env.PY_PROVIDER)
result = await service.call("highlight_code", "print(1)")
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Python RPC provider shape | Caveated | Local provider and TS consumer examples verify the core path. |
| Deployed cross-worker call | Remote-only | Prepared `service-bindings` profile verifies deployed Service Binding RPC. |
| Auth/error policy patterns | Not covered | Future example work. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
