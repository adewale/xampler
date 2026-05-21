# BYOK, secrets, and AI Gateway strategy for expensive examples

## Goal

Let users run real, paid AI/provider examples without ever putting provider keys or account tokens in this repository, in committed source, or in example configuration files.

Local examples should remain deterministic by default. Real calls should stay opt-in, remote-gated, and explicit about cost.

## Findings

### Worker secrets

Cloudflare Worker secrets are encrypted bindings attached to one Worker. They are read at runtime from `env`, and are set with:

```bash
npx wrangler secret put SECRET_NAME
```

They are appropriate for per-Worker secrets such as API tokens used by a deployed example. Wrangler also supports declaring required secret names so deploy/upload fails clearly if a secret is missing.

For local development, secret files such as `.dev.vars` can be used, but in this repo `.dev.vars` and `.env` are ignored and must remain untracked.

### Secrets Store

Cloudflare Secrets Store is account-level secret storage. The Cloudflare docs describe it as the backing store used by AI Gateway BYOK, and as the option to consider when secrets need to be reused across Workers or account features.

For xampler, Secrets Store is attractive for advanced/organizational workflows, but the lowest-friction path is still:

1. local deterministic demo, no secrets;
2. deployed Worker with `wrangler secret put`, no committed secrets;
3. AI Gateway BYOK for provider keys where supported.

### AI Gateway BYOK

AI Gateway BYOK lets users store AI provider API keys in the Cloudflare dashboard under **AI Gateway → Provider Keys**. The provider key is stored securely via Secrets Store and referenced by the gateway.

With BYOK, applications stop sending provider keys such as `Authorization: Bearer OPENAI_API_KEY`. Requests still authenticate to AI Gateway using `cf-aig-authorization: Bearer <AI Gateway token>`.

BYOK supports multiple keys per provider using aliases. The default alias is used unless the request includes:

```text
cf-aig-byok-alias: testing
```

This gives xampler a clean split:

- the user's provider key lives in Cloudflare AI Gateway / Secrets Store;
- the Worker only needs permission to call the gateway;
- the repo never receives the provider key.

### AI binding and unified billing

Cloudflare's Workers AI binding can call Workers AI and third-party models through AI Gateway/unified billing. For third-party models through the AI binding, Cloudflare manages provider credentials and charges the user's Cloudflare account. Users do not provide provider keys.

Important limitation: Cloudflare docs say BYOK is **not supported** for third-party models called through the AI binding. To use BYOK provider keys, examples should use the AI Gateway REST API / chat completions endpoint, not `env.AI.run()`.

## Recommended xampler model

### 1. Keep local verification secret-free

Every expensive example should keep a deterministic local route, e.g. `/demo`, that proves app behavior without account credentials.

```bash
uv run xc examples verify agents
uv run xc examples verify gutenberg
```

This is already the right pattern.

### 2. Separate real-provider modes

Use three explicit modes for AI examples:

| Mode | Secret exposure | Best for |
|---|---:|---|
| `demo` | none | local docs, CI, default verifier |
| `worker-secret` | Worker has provider key secret | simple deployed smoke tests |
| `ai-gateway-byok` | Worker has only AI Gateway auth; provider key is stored in AI Gateway | preferred paid/provider path |
| `ai-binding-unified-billing` | no provider key; Cloudflare bills account | Workers AI / supported third-party model demos through binding |

### 3. Prefer BYOK for third-party provider examples

For examples that call OpenAI/Anthropic/etc., make BYOK the recommended real path:

1. User creates or selects AI Gateway.
2. User enables authenticated gateway access.
3. User stores provider key under Provider Keys in AI Gateway.
4. User optionally sets a BYOK alias such as `xampler-demo`.
5. xampler Worker calls AI Gateway without provider auth.

Runtime secrets/vars should be:

```text
ACCOUNT_ID             plain var or inferred during prepare
GATEWAY_ID             plain var
AI_GATEWAY_TOKEN       Worker secret, Cloudflare AI Gateway token
BYOK_ALIAS             optional plain var, e.g. xampler-demo
MODEL                  plain var, e.g. openai/gpt-4o-mini
```

No `OPENAI_API_KEY` should be needed in the Worker for the BYOK path.

### 4. Keep direct provider-key mode as a fallback, not the default

Direct provider secrets can remain supported for users who do not want BYOK yet:

```bash
npx wrangler secret put OPENAI_API_KEY
```

But docs and setup prompts should label this as fallback. The preferred path should be BYOK because it removes provider keys from Worker runtime configuration and centralizes rotation.

### 5. Add a dedicated BYOK client shape

Current `xampler.ai_gateway.AIGateway` sends provider auth as:

```text
authorization: Bearer <provider api key>
```

For BYOK we need a second mode or constructor that sends:

```text
cf-aig-authorization: Bearer <AI Gateway token>
content-type: application/json
# optionally:
cf-aig-byok-alias: <alias>
```

and intentionally does **not** send provider `Authorization`.

Suggested API:

```python
gateway = AIGateway.byok(
    account_id=account_id,
    gateway_id=gateway_id,
    gateway_token=env.AI_GATEWAY_TOKEN,
    byok_alias=getattr(env, "BYOK_ALIAS", None),
)
```

or:

```python
gateway = AIGateway(
    account_id=account_id,
    gateway_id=gateway_id,
    auth=AIGatewayAuth.byok(gateway_token, alias="xampler-demo"),
)
```

### 6. Update remote prepare behavior

`xc remote prepare ai-gateway` should support two paths:

#### BYOK preferred

Required:

```text
XAMPLER_RUN_REMOTE=1
XAMPLER_PREPARE_REMOTE=1
XAMPLER_REMOTE_AI_GATEWAY=1
CLOUDFLARE_ACCOUNT_ID or wrangler whoami
XAMPLER_AI_GATEWAY_ID
XAMPLER_AI_GATEWAY_TOKEN
```

Optional:

```text
XAMPLER_AI_GATEWAY_BYOK_ALIAS
XAMPLER_AI_GATEWAY_MODEL
```

Prepare should set only Worker secrets needed to call AI Gateway, not provider keys:

```bash
printf '%s' "$XAMPLER_AI_GATEWAY_TOKEN" | npx wrangler secret put AI_GATEWAY_TOKEN
```

#### Direct fallback

Required:

```text
OPENAI_API_KEY
```

Prepare sets `OPENAI_API_KEY` as a Worker secret, but docs should discourage using this when BYOK is available.

### 7. Harden against accidental leakage

Rules to keep:

- never write secrets to `.xampler-remote-state.json`;
- never echo secret values in prepare scripts;
- never put provider keys in `wrangler.jsonc` `vars`;
- never use committed `.dev.vars` or `.env`;
- docs should use placeholder names only;
- verifiers should print redacted diagnostics;
- examples should expose `/demo` locally and skip real routes without opt-in flags.

## Example user journey

```bash
# 1. Create/select AI Gateway in Cloudflare dashboard.
# 2. In AI Gateway, add Provider Key for OpenAI with alias xampler-demo.
# 3. Create an authenticated gateway token with AI Gateway Run permission.

npx --yes wrangler login
export XAMPLER_RUN_REMOTE=1
export XAMPLER_PREPARE_REMOTE=1
export XAMPLER_REMOTE_AI_GATEWAY=1
export XAMPLER_AI_GATEWAY_ID=my-gateway
export XAMPLER_AI_GATEWAY_TOKEN=...       # shell only; not committed
export XAMPLER_AI_GATEWAY_BYOK_ALIAS=xampler-demo
export XAMPLER_AI_GATEWAY_MODEL=openai/gpt-4o-mini

uv run xc remote prepare ai-gateway
uv run xc remote verify ai-gateway
```

The provider key never enters the repository or Worker source. It lives in AI Gateway Provider Keys / Secrets Store.

## Implementation backlog

1. Add BYOK auth support to `xampler.ai_gateway`.
2. Update `examples/ai-agents/ai-gateway-chat` to support `/demo`, `/byok`, and direct fallback only if `OPENAI_API_KEY` exists.
3. Update `docs/api/reference/ai-gateway.md` with BYOK-first guidance.
4. Update `docs/runtime/credentials.md` and `docs/runtime/remote-verification.md` to replace `OPENAI_API_KEY` as the primary AI Gateway path.
5. Add `prepare_remote_examples.py ai-gateway` support for setting only `AI_GATEWAY_TOKEN` in BYOK mode.
6. Add `xc doctor ai-gateway` checks for BYOK vs direct fallback.
7. Verify remote BYOK only when a user supplies gateway/token/alias; local tests remain deterministic.
