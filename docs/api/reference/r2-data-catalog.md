# R2 Data Catalog

## Import

```python
from xampler.r2_data_catalog import R2DataCatalog
```

## Copy this API

```python
catalog = R2DataCatalog(uri=catalog_uri, token=token)
namespaces = await catalog.list_namespaces()
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Demo namespace/table listing | Demo-only | Fixture catalog validates local shape. |
| Real namespace/table listing | Remote-only | Prepared remote profile calls the real Iceberg REST endpoint. |
| Temporary create-list-delete lifecycle | Remote-only | Remote verifier asserts lifecycle response shape. |
| Append/read/schema evolution/snapshots | Not covered | Future PyIceberg/data examples. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
