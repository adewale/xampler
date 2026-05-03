# Credential model

Xampler uses a predictable credential model:

## Local examples

Local verification should work without paid/account credentials whenever possible. Examples use deterministic `Demo*` clients for products that cannot run locally.

```bash
uv run xc verify r2
uv run xc verify kv
```

## Remote examples

Remote verification is always opt-in:

```bash
XAMPLER_RUN_REMOTE=1 xc remote verify vectorize
```

Preparation and cleanup have separate gates:

```bash
XAMPLER_RUN_REMOTE=1 XAMPLER_PREPARE_REMOTE=1 xc remote prepare vectorize
XAMPLER_RUN_REMOTE=1 XAMPLER_CLEANUP_REMOTE=1 xc remote cleanup vectorize
```

## Common credentials

| Variable | Used for |
|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | Account-scoped REST APIs and some prepare scripts. |
| `CLOUDFLARE_API_TOKEN` | Wrangler/API operations such as Browser Rendering prepare. |
| `WRANGLER_R2_SQL_AUTH_TOKEN` | R2 SQL. |
| `XAMPLER_R2_DATA_CATALOG_TOKEN` | R2 Data Catalog/Iceberg REST API. |
| `OPENAI_API_KEY` | AI Gateway OpenAI-compatible demo. |
| `XAMPLER_AI_GATEWAY_MODEL` | Optional AI Gateway model override; default is `openai/gpt-4o-mini`. |

Use `wrangler secret put` for Worker runtime secrets. Do not commit tokens or put paid remote checks on by default.

## Doctor

```bash
xc doctor
xc doctor r2-sql
```

`doctor` reports local tools, remote gates, profile-specific credential names, and cost warnings.
