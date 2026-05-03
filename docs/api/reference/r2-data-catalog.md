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

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
