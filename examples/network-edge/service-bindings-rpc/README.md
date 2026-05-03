# Service Bindings 13 — RPC

Python RPC service plus TypeScript client shape. Python side exposes a typed `highlight_code` method.

## Cloudflare docs

- [Service Bindings](https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/)

## Copy this API

```python
from xampler.service_bindings import ServiceBinding

service = ServiceBinding(env.PY_PROVIDER)
result = await service.call("highlight_code", "print(1)")
```
