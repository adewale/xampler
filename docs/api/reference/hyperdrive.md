# Hyperdrive

## Import

```python
from xampler.hyperdrive import DemoPostgres, HyperdriveConfig, HyperdrivePostgres, PostgresQuery
```

## Copy this API

```python
config = HyperdriveConfig.from_binding(env.HYPERDRIVE)
client = HyperdrivePostgres(config)
result = await client.query(PostgresQuery("SELECT now()"))
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Binding config parsing | Supported | `HyperdriveConfig.from_binding()` keeps runtime config visible. |
| Demo Postgres query | Demo-only | Local verification validates query/result shape. |
| Real Postgres/Hyperdrive query | Remote-only | Requires deployed Worker and a real Postgres database. |
| Transactions/pooling notes | Not covered | Future production example. |


## Testability

Use `DemoPostgres` and `PostgresQuery.validate_read_only()` locally. Real Hyperdrive still needs a Postgres database and deployed Worker credentials.
