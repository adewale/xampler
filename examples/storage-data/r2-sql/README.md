# R2 SQL 21 — Query

Pythonic SQL request builder for the R2 SQL HTTP API.

Local `/demo` verification checks read-only SQL shaping without credentials. For real remote verification, run the prepared deployed flow; the prepare script creates/enables the R2 bucket/catalog, infers `ACCOUNT_ID` from `wrangler whoami`, stores `ACCOUNT_ID` and `CF_API_TOKEN` as Worker secrets, deploys the Worker, and records the deployed URL.

```bash
npx --yes wrangler login
WRANGLER_R2_SQL_AUTH_TOKEN=... \
XAMPLER_RUN_REMOTE=1 XAMPLER_PREPARE_REMOTE=1 \
  uv run python scripts/prepare_remote_examples.py r2-sql
XAMPLER_RUN_REMOTE=1 XAMPLER_REMOTE_R2_SQL=1 \
  uv run python scripts/verify_remote_examples.py r2-sql
```

## Cloudflare docs

- [R2 SQL](https://developers.cloudflare.com/r2-sql/)

## Copy this API

```python
from xampler.r2_sql import R2SqlClient, R2SqlQuery

client = R2SqlClient(account_id=account_id, bucket_name=bucket, token=token)
result = await client.query(R2SqlQuery("SHOW TABLES IN xampler"))
```
