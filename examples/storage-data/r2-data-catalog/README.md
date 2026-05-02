# R2 Data Catalog 22 — Iceberg REST

Lists namespaces/tables through the Iceberg REST Catalog API.

Local `/demo` verification returns a deterministic catalog fixture. For real remote verification, run the prepared deployed flow; the prepare script creates/enables the R2 bucket/catalog, stores `CATALOG_URI` and `CATALOG_TOKEN` as Worker secrets, deploys the Worker, and records the deployed URL.

```bash
npx --yes wrangler login
XAMPLER_R2_DATA_CATALOG_TOKEN=... \
XAMPLER_RUN_REMOTE=1 XAMPLER_PREPARE_REMOTE=1 \
  uv run python scripts/prepare_remote_examples.py r2-data-catalog
XAMPLER_RUN_REMOTE=1 XAMPLER_REMOTE_R2_DATA_CATALOG=1 \
  uv run python scripts/verify_remote_examples.py r2-data-catalog
```

If your `WRANGLER_R2_SQL_AUTH_TOKEN` also has Data Catalog permissions, the prepare script can use it instead of `XAMPLER_R2_DATA_CATALOG_TOKEN`.

## Cloudflare docs

- [R2 Data Catalog](https://developers.cloudflare.com/r2/data-catalog/)
