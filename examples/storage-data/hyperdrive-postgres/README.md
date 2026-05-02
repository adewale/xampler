# Hyperdrive 25 — Postgres from Python Workers

A Pythonic Hyperdrive example for Postgres-backed applications.

The local verifier uses a deterministic `DemoPostgres` transport so the API shape is executable without a database. The real `/query` route shows how a Hyperdrive binding supplies connection metadata for a Postgres client in deployed Workers.

```bash
uv run pywrangler dev
uv run python ../scripts/verify_examples.py examples/storage-data/hyperdrive-postgres
```

## API shape

- `HyperdriveConfig.from_binding(env.HYPERDRIVE)` keeps Cloudflare's binding vocabulary visible.
- `PostgresQuery` and `PostgresResult` are typed dataclasses.
- `HyperdrivePostgres.query()` is the production-facing service wrapper.
- `DemoPostgres` verifies query validation and result shape locally.

## Cloudflare docs

- [Hyperdrive](https://developers.cloudflare.com/hyperdrive/)
