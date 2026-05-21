# R2 SQL

## Import

```python
from xampler.r2_sql import R2SqlClient, R2SqlQuery
```

## Copy this API

```python
client = R2SqlClient(account_id=account_id, bucket_name=bucket, token=token)
result = await client.query(R2SqlQuery("SHOW TABLES IN xampler"))
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Read-only `SELECT`/`SHOW`/`EXPLAIN` shaping | Supported | Local demo verifies guards and automatic `LIMIT`. |
| Real R2 SQL query | Remote-only | Prepared remote profile queries the seeded catalog/table. |
| Mutations and joins | Unsupported / throws | Example guard rejects mutating SQL and joins. |
| Rich schema discovery/query builder | Not covered | Future wrapper work. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
