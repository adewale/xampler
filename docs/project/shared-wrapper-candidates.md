# Shared Wrapper Package Candidates

Last reviewed: 2026-05-02.

Xampler should lift only stable, boring, repeated concepts into `xampler/`. Product hero logic should stay in examples until it has proved itself across multiple primitives.

## Already shared

| Module | Contents |
|---|---|
| `xampler.streaming` | `ByteStream`, `RecordStream`, `JsonlReader`, `aiter_batches`, `StreamCheckpoint`, `AgentEvent`. |
| `xampler.types` | `JsonObject`, `R2Key`, `QueueName`, `WorkflowId`, `VectorId`, `AgentId`, `SupportsRaw`, `DemoTransport`, `RemoteVerifier`. |

## Best candidates to extract next

| Candidate module | Repeated concepts | Why now |
|---|---|---|
| `xampler.response` | JSON/text/error response helpers, content-type constants | Repeated in many `entry.py` files and low risk. |
| `xampler.status` | `OperationState`, `Progress`, `Checkpoint`, `BatchResult` | HVSC, Workflows, Agents, streaming, queues all use status/progress. |
| `xampler.testing` | verifier process helpers, remote-skip conventions, env guards | `scripts/verify_examples.py` is growing custom cases. |
| `xampler.bindings` | tiny base `BindingService`, `ResourceHandle`, `SupportsRaw` | Common wrapper shape without hiding product vocabulary. |
| `xampler.demo` | `DemoTransport` conventions and route naming | Account-backed products use the same real/demo split. |

## Do not extract yet

| Keep local | Reason |
|---|---|
| `R2Bucket`, `D1Database`, `QueueService`, `VectorIndex` product wrappers | They are still tutorial-specific and should stay readable in their examples. |
| Cloudflare REST clients | Product-specific auth/metadata varies too much. |
| Demo product logic | Useful to read beside the example it supports. |

## Extraction rule

Extract when all are true:

1. the pattern appears in at least three examples;
2. the shared abstraction is smaller than the duplicated code;
3. it does not hide Cloudflare product vocabulary;
4. it can be covered by strict `pyright` and unit tests.
