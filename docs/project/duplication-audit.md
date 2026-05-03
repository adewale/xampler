# Duplication audit

Latest audit focus: wrapper-like code duplicated between examples and `xampler/`.

## High-priority duplicates

| Area | Finding | Recommendation |
|---|---|---|
| HVSC full app | Migrated away from local `D1Database`, `QueueService`, and `DemoVectorIndex` equivalents. It now uses `xampler.d1`, `xampler.queues`, `xampler.r2`, and `xampler.vectorize`; only HVSC domain orchestration remains local. | Add route-level tests around the HVSC pipeline and consider extracting reusable dataset-pipeline helpers later. |
| Response helpers | Several examples had local `json_response`, `text_response`, or `response`. | Use `xampler.response.{json_response,text_response,html_response,binary_response}`. |
| Gutenberg | Local `BatchResult` and `DemoAIService` overlapped library names. | Use `xampler.status.BatchResult` and `xampler.ai.DemoAIService`; keep Gutenberg-specific sinks/sessions local. |

## Newly migrated shared surfaces

| Surface | Module |
|---|---|
| Durable Object namespace/ref | `xampler.durable_objects` |
| Workflows service/status | `xampler.workflows` |
| Cron/scheduled event result | `xampler.cron` |
| Service Binding RPC wrapper | `xampler.service_bindings` |
| WebSocket status/demo session | `xampler.websockets` |
| Agents message/run result/demo | `xampler.agents` |
| AI Gateway chat request/response/demo | `xampler.ai_gateway` |

## Intentional local code

Do not migrate:

- `Default.fetch` handlers;
- HTML and UI strings;
- fixture-specific verifier endpoints;
- app-specific dataclasses like `Track`, `HvscRelease`, `TextRecord`;
- one-off orchestration that is not reusable outside the example.

## Why the migration is not finished

The remaining local surfaces are either app-specific or still need stronger realism before they become stable APIs. Hyperdrive needs a real Postgres/Hyperdrive story. Email and HTMLRewriter need more than one route shape. Durable Object chat/WebSocket hibernation should not be overfit to a single counter or chatroom.
