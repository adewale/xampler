# Tier 1 Completion Plan

Last reviewed: 2026-05-02.

Goal: every example in the README primitive table should reach Tier 1 by having credible coverage, a Pythonic API surface, and at least meaningful executable verification. Tier 1 does **not** require every account-backed product to run in CI without credentials, but it does require one of:

1. deterministic local verification that exercises the same Python wrapper shape, plus a documented remote path; or
2. an env-gated remote verifier that hits real Cloudflare resources; ideally both.

## Current non-Tier-1 examples

| Primitive | Current blocker | Tier 1 requirement |
|---|---|---|
| Service Bindings / RPC | Multi-worker flow is not one-command verified. | Add one-command local harness that starts provider + consumer, calls typed RPC, verifies success/error cases. |
| Outbound WebSockets | Depends on external network; no deterministic local fake stream. | Add local WebSocket test server or deterministic Durable Object seam, verify connect/message/reconnect/status. |
| Browser Rendering | Static/client shape only unless real account token exists. | Add `DemoBrowserRenderer` for local shape + env-gated remote Browser Rendering verification for screenshots/PDF/content. |
| Email Workers | No deterministic email event harness. | Add `EmailEvent` fixture harness that verifies reject/forward/reply decisions and MIME parsing. |
| AI Gateway | No real or deterministic gateway verification. | Add demo gateway transport and env-gated remote AI Gateway verification including metadata/cache/error shape. |
| R2 Data Catalog | Lists only; no create/append/read story. | Add PyIceberg-oriented client shape, deterministic catalog fixture, and env-gated real catalog listing/table verifier. |
| LangChain/package orchestration | Placeholder service-boundary example, not a real workload. | Replace with a real LangChain-compatible or LCEL-style Worker example, or remove from the primitive tier table. |

## API surface changes to feed back from HVSC

The complex HVSC flow showed that examples become easier to compose when every primitive exposes the same small set of affordances:

- typed request and result dataclasses;
- a service wrapper whose constructor takes the platform binding/client;
- resource handles for named resources (`bucket.object(key)`, `namespace.key(name)`, `workflow.instance(id)`);
- explicit local/demo transports for account-backed products;
- env-gated real transports for remote verification;
- `.raw` escape hatch for newly released Cloudflare APIs;
- progress/status models for long-running operations;
- UI or CLI flows that can recover from missing setup.

## Missing Cloudflare Developer Platform primitives

The repository covers many core Workers primitives, but it does not yet have dedicated examples for these Developer Platform products/capabilities:

| Missing primitive/product | Proposed example | Notes |
|---|---|---|
| Workers Analytics Engine | `analytics-engine-25-events` | Write/query event analytics from Workers; useful for telemetry and dataset-search analytics. |
| Hyperdrive | `hyperdrive-26-postgres` | Python DB client pattern for Postgres through Hyperdrive; important for existing app migrations. |
| Workers Builds / Deploy Hooks | `workers-builds-27-ci` | Build/deploy lifecycle example; mostly tooling/config rather than runtime API. |
| Secrets Store / environment secrets | `secrets-28-config` | Typed config loader, secret validation, local `.dev.vars` vs deployed secrets. |
| Static forms / Turnstile integration | `turnstile-29-forms` | Developer-facing bot protection flow for Workers/Pages apps. |
| Rate Limiting binding/rules integration | `rate-limiting-30-guard` | Request guard wrapper with deterministic local limiter. |
| Cloudflare Images API | `cloudflare-images-31-transform` | Current `images-12` is Pillow/binary response, not Cloudflare Images product coverage. |
| Stream | `stream-32-video` | Upload/status/playback token patterns for video workflows. |
| Calls / Realtime SFU | `calls-33-realtime` | WebRTC/realtime media APIs; account-backed, likely remote verifier only. |
| Pub/Sub | `pubsub-34-mqtt` | MQTT publish/subscribe flow if available to the account. |
| Workers for Platforms / Dispatch Namespaces | `dispatch-35-platforms` | Multi-tenant Worker dispatch; advanced but core platform capability. |
| Logpush / Observability APIs | `observability-36-logs` | Account API example for shipping/querying logs; useful for production apps. |
| Cache API | `cache-37-edge-cache` | Workers Cache API is used implicitly elsewhere but deserves a direct Pythonic wrapper example. |
| URLPattern / routing helpers | `routing-38-urlpattern` | Small runtime primitive for Python Workers request routing. |
| Tail Workers | `tail-workers-39-observability` | Dedicated observability Worker receiving events. |

Some Cloudflare products such as DNS, WAF, Access, Zero Trust, and Registrar are Cloudflare APIs but are less central to the Workers Developer Platform runtime. They can be added later as account/API examples, but the table above is the higher-priority gap list for Xampler.

## Execution order

1. Promote existing Tier 4 examples before adding new products.
2. Replace or remove `ai-05-langchain`; do not keep a placeholder in the scored table.
3. Add missing primitives in dependency order: Cache API, Analytics Engine, Hyperdrive, Secrets/config, Turnstile, Cloudflare Images.
4. Add env-gated remote verification profiles for account-backed examples.
5. Keep README, `docs/primitives-api-surface.md`, and `docs/primitive-test-realism.md` synchronized after each promotion.
