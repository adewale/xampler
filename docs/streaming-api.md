# Streaming API Surface

Last reviewed: 2026-05-02.

Streaming is now a first-class Xampler API shape. The goal is that R2 objects, JSONL datasets, AI/gateway responses, Agents, WebSockets, D1 sinks, and Queue/Vectorize batches can be composed without reading everything into memory.

## Required streaming vocabulary

| Suggestion | Implemented surface | Example |
|---|---|---|
| 1. Object streams | `ByteStream.iter_bytes()`, `iter_text()`, `iter_lines()` | `examples/streaming/gutenberg-stream-composition` |
| 2. JSONL records | `JsonlReader.records()` | `examples/streaming/gutenberg-stream-composition /events` |
| 3. Batching | `aiter_batches(records, size=...)` | `examples/streaming/gutenberg-stream-composition /demo` |
| 4. Stream-to-D1 style sink | `DemoD1Sink.insert_batch()` + checkpoints | `examples/streaming/gutenberg-stream-composition /demo` |
| 5. Agent streaming | `DemoAgentSession.stream() -> AgentEvent` | `examples/streaming/gutenberg-stream-composition /events` |
| 6. AI/gateway token streaming | `DemoAIService.stream_text()` | `examples/streaming/gutenberg-stream-composition /events` |
| 7. WebSocket session stream | `DemoWebSocketSession.__aiter__()` | `examples/streaming/gutenberg-stream-composition /events` |
| 8. Resumable checkpoints | `StreamCheckpoint` | `examples/streaming/gutenberg-stream-composition /demo` |

## Stream-to-stream target

```python
byte_stream = ByteStream(r2.object(key).iter_bytes())
records = JsonlReader(byte_stream.iter_lines()).records()

async for batch in aiter_batches(records, size=500):
    await db.insert_batch(batch)
    await progress.checkpoint(batch)
```

The current executable proof is `examples/streaming/gutenberg-stream-composition`, which uses Project Gutenberg's Shakespeare archive as the golden large-file source:

```text
r2://xampler-datasets/gutenberg/100/raw/pg100-h.zip
```

## Next integration work

The streaming types are currently demonstrated in one example. The next refactor should lift them into a shared package used by R2, Agents, AI Gateway, Workers AI, WebSockets, D1, Queues, Vectorize, and Workflows.
