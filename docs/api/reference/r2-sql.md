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

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
