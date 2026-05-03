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

## Testability

Use `DemoPostgres` and `PostgresQuery.validate_read_only()` locally. Real Hyperdrive still needs a Postgres database and deployed Worker credentials.
