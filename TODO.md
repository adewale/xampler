# TODO: Real remote verification prerequisites

Last updated: 2026-05-02.

After `npx --yes wrangler login`, all local checks and local example verifiers passed. Remote verification showed that Wrangler OAuth is necessary, but not sufficient, for every product. This file tracks what we still need to solve for real account-backed testing.

## Need a better solution

These profiles still need a design that is safer or more automated before a normal contributor can run them with only documented setup steps.

- [ ] `ai-gateway` — missing `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `XAMPLER_AI_GATEWAY_ID`, `OPENAI_API_KEY`.
  - Decide whether this remains a secrets-required profile or whether we can add an AI Gateway + Workers AI binding example that avoids provider keys.
  - If provider-backed Gateway stays, keep it explicitly secret-gated; `wrangler login` cannot inject provider keys into Worker `fetch()` calls.
- [ ] `analytics-engine` — missing deployed URL.
  - Add a direct Workers Analytics Engine example first, then add deploy/prep steps and a remote verifier route.
- [ ] `hyperdrive` — missing deployed URL.
  - Needs a real Postgres database plus a Hyperdrive config. Figure out whether the example should document bring-your-own-Postgres, use a disposable hosted Postgres, or remain URL-gated.
- [ ] `images` — missing deployed URL.
  - Add a direct Cloudflare Images product API example first, then decide whether the remote verifier uses REST API credentials, a deployed Worker URL, or both.

## Prepare prerequisites as part of examples

For the remaining remote profiles, Cloudflare docs suggest concrete setup commands or topology that can be folded into example-specific prepare paths. `scripts/prepare_remote_examples.py` now exists and covers the first set of Wrangler-managed prerequisites.

### `workers-ai`

Docs pattern:

- Add an AI binding in `wrangler.jsonc`: `{"ai": {"binding": "AI"}}`.
- Run `npx wrangler login`.
- Run `wrangler dev`; Workers AI bindings access Cloudflare remotely even during local dev and can incur usage.

Current result:

- Remote preview started and exposed `env.AI`, but verifier readiness calls returned `403 Forbidden` on `/demo`.

TODO:

- [ ] Investigate whether `pywrangler dev --remote` is the wrong mode for AI binding verification now that Wrangler supports remote bindings differently.
- [ ] Try plain `uv run pywrangler dev` with the AI binding, matching Cloudflare's Workers AI docs more closely.
- [ ] Change readiness to a non-AI `/health` route if the remote preview blocks `/demo` differently from local dev.
- [ ] Keep the only required env as `XAMPLER_RUN_REMOTE=1` and `XAMPLER_REMOTE_WORKERS_AI=1` if `wrangler login` is enough.

### `vectorize`

Docs pattern:

```bash
npx wrangler vectorize create <INDEX_NAME> --dimensions=<N> --metric=<euclidean|cosine|dot-product>
```

Then bind it in `wrangler.jsonc`:

```jsonc
{
  "vectorize": [{"binding": "INDEX", "index_name": "xampler-vectorize"}]
}
```

Current result:

- Wrangler OAuth worked, but Cloudflare returned: `Vectorize binding 'INDEX' references index 'xampler-vectorize' which was not found`.

TODO:

- [x] Add a prepare step for `examples/ai-agents/vectorize-search`:

  ```bash
  npx wrangler vectorize create xampler-vectorize --dimensions=32 --metric=cosine
  ```

- [x] Make the command idempotent: describe/list first, create only if absent.
- [x] Ensure fixture vectors and index dimensions stay in sync.
- [x] Deploy the Vectorize Worker and record its URL so verification avoids `wrangler dev --remote` 403 preview issues.
- [ ] Optionally add metadata index creation if future tests use metadata filters.

### `browser-rendering`

Docs pattern:

- REST API: call `https://api.cloudflare.com/client/v4/accounts/{accountId}/browser-rendering/...` with a token that has Browser Rendering permission.
- Worker binding: add `{"browser": {"binding": "MYBROWSER"}}` and use Cloudflare's Puppeteer/Playwright libraries from Workers.

Current state:

- The Python example uses the REST API, so Worker code needs `ACCOUNT_ID` and `CF_API_TOKEN` in `.dev.vars`.

TODO:

- [ ] Decide whether to keep REST API coverage or add a Browser Rendering binding variant.
- [ ] If REST stays: add a prep/preflight command that reads account ID from Wrangler where possible, then clearly asks only for the API token.
- [ ] If binding variant is possible from Python Workers: add a `browser` binding and verify through Wrangler auth instead of a Worker-held API token.

### `r2-sql`

Docs pattern:

1. Create an R2 bucket:

   ```bash
   npx wrangler r2 bucket create xampler-r2-sql
   ```

2. Enable R2 Data Catalog on that bucket:

   ```bash
   npx wrangler r2 bucket catalog enable xampler-r2-sql
   ```

3. Create an R2 API token with R2 Data Catalog, R2 storage, and R2 SQL permissions.
4. Query with `WRANGLER_R2_SQL_AUTH_TOKEN` or pass the token to the REST API.

TODO:

- [x] Add a prepare script that creates the bucket and enables catalog idempotently.
- [ ] Add a tiny seed pipeline/table or documented fixture so `SHOW DATABASES` is not the only real query.
- [x] Use Cloudflare's `WRANGLER_R2_SQL_AUTH_TOKEN` env name where possible; map it to Worker `.dev.vars` only for REST-backed Worker tests.
- [ ] Keep token creation manual unless Cloudflare exposes a safe Wrangler OAuth flow for this permission.

### `r2-data-catalog`

Docs pattern:

- Enable R2 Data Catalog on an R2 bucket.
- Use the Iceberg REST Catalog URI and bearer token.
- Common endpoint shape: `https://<account-id>.r2.cloudflarestorage.com/iceberg/<bucket-name>`.

TODO:

- [x] Reuse the `r2-sql` bucket/catalog prepare step where possible.
- [ ] Add a small namespace/table creation path or a read-only catalog smoke test.
- [x] Record `XAMPLER_R2_DATA_CATALOG_URI` equivalent in prepared state and document/export the token requirement.
- [ ] Keep catalog token manual unless a safe Wrangler-backed token path exists.

### `queues-dlq`

Docs pattern:

```bash
npx wrangler queues create xampler-jobs
npx wrangler queues create xampler-jobs-dlq
```

Consumer config supports:

```jsonc
{
  "queues": {
    "consumers": [{
      "queue": "xampler-jobs",
      "dead_letter_queue": "xampler-jobs-dlq"
    }]
  }
}
```

TODO:

- [x] Add a prepare step for `examples/state-events/queues-producer-consumer` that creates both queues if missing.
- [x] Deploy the Worker after queue creation.
- [x] Replace the deployed-URL-only remote profile with a profile that can use prepared state.
- [ ] Verify real async consumer retry and DLQ behavior with bounded polling. Current remote route verifies deployed producer enqueueing.

### `service-bindings`

Docs pattern:

- Service bindings require the target Worker to exist in the account.
- Deploy provider Worker first, then deploy caller Worker with a `services` binding to the provider.
- For local dev, run both Workers; for remote verification, deploy both.

TODO:

- [x] Add a prepare step that deploys `examples/network-edge/service-bindings-rpc/py` first.
- [x] Then deploy `examples/network-edge/service-bindings-rpc/ts` with its binding to `xampler-network-edge-service-bindings-rpc-py`.
- [x] Make remote verifier call the deployed TS consumer URL from prepared state instead of requiring `XAMPLER_REMOTE_SERVICE_BINDINGS_URL` manually.

### `websockets`

Docs pattern from our example topology:

- Durable Object backed WebSockets need a deployed Worker with Durable Object binding and migration.
- The example already has `durable_objects` binding and `new_sqlite_classes` migration in Wrangler config.

TODO:

- [x] Add a prepare/deploy step for `examples/state-events/durable-object-chatroom`.
- [x] Discover or print the deployed workers.dev URL.
- [x] Reuse the existing two-client WebSocket broadcast verifier against the deployed URL.

## Cross-cutting TODOs

- [x] Add `scripts/prepare_remote_examples.py` with profile-specific, idempotent setup.
- [ ] Prefer `wrangler login`/Wrangler OAuth for resource creation whenever Cloudflare supports it.
- [ ] Keep secrets out of generated files; temporary `.dev.vars` must be restored or deleted.
- [ ] Separate three phases: `prepare`, `verify`, and `cleanup`.
- [ ] Never auto-create paid resources unless `XAMPLER_RUN_REMOTE=1` and a profile-specific prepare flag are set.
- [ ] Update `docs/runtime/remote-verification.md` once each profile has a real prepare path.
