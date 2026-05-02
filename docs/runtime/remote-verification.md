# Remote Verification

Some examples keep deterministic local `/demo` routes because the real product needs Cloudflare account resources, secrets, paid entitlements, or deployed Workers. Remote verification is intentionally separate from local verification and never runs by default.

## Safety rules

Remote profiles may cost money. Every profile requires all of the following:

1. `XAMPLER_RUN_REMOTE=1`
2. a profile-specific enable flag, for example `XAMPLER_REMOTE_WORKERS_AI=1`
3. either normal Wrangler authentication (`wrangler login`) or profile-specific credentials/deployed URLs

If anything is missing, the verifier prints `SKIP ...` and exits successfully. For profiles that use Wrangler remote bindings, `wrangler login` is the intended local developer credential path; `CLOUDFLARE_API_TOKEN` is mainly for CI or for examples whose Worker code calls Cloudflare REST APIs directly.

## List profiles

```bash
uv run python scripts/verify_remote_examples.py --list
```

## Show required environment for a profile

```bash
uv run python scripts/verify_remote_examples.py workers-ai --show-env
uv run python scripts/verify_remote_examples.py vectorize --show-env
```

## Profiles that run real mechanisms from the examples

These profiles start the example Worker and call its real route. Binding-backed products use Wrangler remote dev where possible; REST-backed products use `.dev.vars` generated temporarily from your shell environment.

| Profile | Mechanism | Required environment beyond `XAMPLER_RUN_REMOTE=1` |
|---|---|---|
| `workers-ai` | real Workers AI binding through Wrangler remote dev | `XAMPLER_REMOTE_WORKERS_AI=1`; authenticate with `wrangler login` first. |
| `vectorize` | real Vectorize binding through Wrangler remote dev; runs describe/upsert/query | `XAMPLER_REMOTE_VECTORIZE=1`; authenticate with `wrangler login` first and ensure the configured Vectorize index exists. |
| `browser-rendering` | real Browser Rendering REST API from the Worker | `XAMPLER_REMOTE_BROWSER_RENDERING=1`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` |
| `r2-sql` | real R2 SQL REST API from the Worker | `XAMPLER_REMOTE_R2_SQL=1`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` |
| `ai-gateway` | real AI Gateway endpoint from the Worker | `XAMPLER_REMOTE_AI_GATEWAY=1`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `XAMPLER_AI_GATEWAY_ID`, `OPENAI_API_KEY` |
| `r2-data-catalog` | real Iceberg/R2 Data Catalog endpoint from the Worker | `XAMPLER_REMOTE_R2_DATA_CATALOG=1`, `XAMPLER_R2_DATA_CATALOG_URI`, `XAMPLER_R2_DATA_CATALOG_TOKEN` |

Example:

```bash
wrangler login
export XAMPLER_RUN_REMOTE=1
export XAMPLER_REMOTE_VECTORIZE=1
uv run python scripts/verify_remote_examples.py vectorize
```

## Deployed URL profiles

The following profiles still require deployed verification routes because the local example is not yet wired to a fully real end-to-end implementation:

| Profile | Enable flag | URL variable | Purpose |
|---|---|---|---|
| `hyperdrive` | `XAMPLER_REMOTE_HYPERDRIVE=1` | `XAMPLER_REMOTE_HYPERDRIVE_URL` | Deployed Hyperdrive/Postgres query route. |
| `images` | `XAMPLER_REMOTE_IMAGES=1` | `XAMPLER_REMOTE_IMAGES_URL` | Deployed Cloudflare Images route. |
| `analytics-engine` | `XAMPLER_REMOTE_ANALYTICS_ENGINE=1` | `XAMPLER_REMOTE_ANALYTICS_ENGINE_URL` | Deployed Analytics Engine route. |
| `queues-dlq` | `XAMPLER_REMOTE_QUEUES_DLQ=1` | `XAMPLER_REMOTE_QUEUES_DLQ_URL` | Deployed Queue delivery/DLQ verification routes. |
| `service-bindings` | `XAMPLER_REMOTE_SERVICE_BINDINGS=1` | `XAMPLER_REMOTE_SERVICE_BINDINGS_URL` | Deployed cross-worker Service Binding route. |
| `websockets` | `XAMPLER_REMOTE_WEBSOCKETS=1` | `XAMPLER_REMOTE_WEBSOCKETS_URL` | Deployed WebSocket verification route. |

## Local checks are still the default

Use the local verifier for normal development:

```bash
uv run python scripts/verify_examples.py --list
uv run python scripts/verify_examples.py examples/start/hello-worker
```
