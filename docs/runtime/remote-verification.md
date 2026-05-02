# Remote Verification

Some examples keep deterministic local `/demo` routes because the real product needs Cloudflare account resources, secrets, paid entitlements, or deployed Workers. Remote verification is intentionally separate from local verification and never runs by default.

## Safety rules

Remote profiles may cost money. Every profile requires all of the following:

1. `XAMPLER_RUN_REMOTE=1`
2. a profile-specific enable flag, for example `XAMPLER_REMOTE_WORKERS_AI=1`
3. profile-specific credentials or deployed URLs

If anything is missing, the verifier prints `SKIP ...` and exits successfully.

## List profiles

```bash
uv run python scripts/verify_remote_examples.py --list
```

## Workers AI remote check

This profile starts the Workers AI example locally and calls its real `/` route, which uses the `AI` binding. It may incur Workers AI usage.

Required environment:

```bash
export XAMPLER_RUN_REMOTE=1
export XAMPLER_REMOTE_WORKERS_AI=1
export CLOUDFLARE_ACCOUNT_ID=...
export CLOUDFLARE_API_TOKEN=...
```

Run:

```bash
uv run python scripts/verify_remote_examples.py workers-ai
```

## Deployed URL profiles

The following profiles are scaffolded around deployed verification URLs. Each needs `XAMPLER_RUN_REMOTE=1`, its profile enable flag, and a profile URL variable.

| Profile | Enable flag | URL variable | Purpose |
|---|---|---|---|
| `ai-gateway` | `XAMPLER_REMOTE_AI_GATEWAY=1` | `XAMPLER_REMOTE_AI_GATEWAY_URL` | Real AI Gateway route. |
| `vectorize` | `XAMPLER_REMOTE_VECTORIZE=1` | `XAMPLER_REMOTE_VECTORIZE_URL` | Real Vectorize route. |
| `browser-rendering` | `XAMPLER_REMOTE_BROWSER_RENDERING=1` | `XAMPLER_REMOTE_BROWSER_RENDERING_URL` | Real Browser Rendering route. |
| `hyperdrive` | `XAMPLER_REMOTE_HYPERDRIVE=1` | `XAMPLER_REMOTE_HYPERDRIVE_URL` | Real Hyperdrive query route. |
| `r2-sql` | `XAMPLER_REMOTE_R2_SQL=1` | `XAMPLER_REMOTE_R2_SQL_URL` | Real R2 SQL route. |
| `r2-data-catalog` | `XAMPLER_REMOTE_R2_DATA_CATALOG=1` | `XAMPLER_REMOTE_R2_DATA_CATALOG_URL` | Real R2 Data Catalog route. |
| `images` | `XAMPLER_REMOTE_IMAGES=1` | `XAMPLER_REMOTE_IMAGES_URL` | Real Cloudflare Images route. |
| `analytics-engine` | `XAMPLER_REMOTE_ANALYTICS_ENGINE=1` | `XAMPLER_REMOTE_ANALYTICS_ENGINE_URL` | Real Analytics Engine route. |
| `queues-dlq` | `XAMPLER_REMOTE_QUEUES_DLQ=1` | `XAMPLER_REMOTE_QUEUES_DLQ_URL` | Deployed Queue delivery/DLQ verification routes. |
| `service-bindings` | `XAMPLER_REMOTE_SERVICE_BINDINGS=1` | `XAMPLER_REMOTE_SERVICE_BINDINGS_URL` | Deployed cross-worker Service Binding route. |
| `websockets` | `XAMPLER_REMOTE_WEBSOCKETS=1` | `XAMPLER_REMOTE_WEBSOCKETS_URL` | Deployed WebSocket verification route. |

Example:

```bash
export XAMPLER_RUN_REMOTE=1
export XAMPLER_REMOTE_VECTORIZE=1
export XAMPLER_REMOTE_VECTORIZE_URL=https://your-worker.example.workers.dev
uv run python scripts/verify_remote_examples.py vectorize
```

## Local checks are still the default

Use the local verifier for normal development:

```bash
uv run python scripts/verify_examples.py --list
uv run python scripts/verify_examples.py examples/start/hello-worker
```
