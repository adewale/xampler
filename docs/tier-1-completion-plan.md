# Tier 1 Completion Plan

Last reviewed: 2026-05-02.

Goal: every example in the README primitive table should reach Tier 1 by having credible coverage, a Pythonic API surface, and at least meaningful executable verification. Tier 1 does **not** require every account-backed product to run in CI without credentials, but it does require one of:

1. deterministic local verification that exercises the same Python wrapper shape, plus a documented remote path; or
2. an env-gated remote verifier that hits real Cloudflare resources; ideally both.

## Current non-Tier-1 examples

All examples currently listed in the README primitive table are Tier 1 by the repository definition: each has a typed/Pythonic surface and an executable local verifier or a deterministic local transport for account-backed APIs.

Remaining promotion work is now about raising **test realism** from level 3 to level 4/5 for account-backed products, not about Tier 1 admission.

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
| Hyperdrive | `hyperdrive-25-postgres` | Added. Python DB client pattern for Postgres through Hyperdrive; important for existing app migrations. |
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
| Agents SDK | `agents-26-sdk` | Added. Stateful agent/session shape with tools and Durable Object routing. |
| URLPattern / routing helpers | `routing-38-urlpattern` | Small runtime primitive for Python Workers request routing. |
| Tail Workers | `tail-workers-39-observability` | Dedicated observability Worker receiving events. |

Some Cloudflare products such as DNS, WAF, Access, Zero Trust, and Registrar are Cloudflare APIs but are less central to the Workers Developer Platform runtime. They can be added later as account/API examples, but the table above is the higher-priority gap list for Xampler.

## Execution order

1. Raise level-3 Tier 1 examples to level 4 with richer deterministic local harnesses.
2. Add env-gated remote verification profiles for account-backed examples.
3. Add missing primitives in dependency order: Cache API, Analytics Engine, Secrets/config, Turnstile, Cloudflare Images.
4. Keep README, `docs/primitives-api-surface.md`, and `docs/primitive-test-realism.md` synchronized after each promotion.
