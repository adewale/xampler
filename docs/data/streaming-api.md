# Streaming API Surface

Last reviewed: 2026-05-02.

Streaming is now a first-class Xampler API shape. The goal is that R2 objects, JSONL datasets, AI/gateway responses, Agents, WebSockets, D1 sinks, and Queue/Vectorize batches can be composed without reading everything into memory.

## Required streaming vocabulary

| Suggestion | Implemented surface | Example |
|---|---|---|
| 1. Object streams | `ByteStream.iter_bytes()`, `iter_text()`, `iter_lines()`, `js_readable_stream_chunks()` | `examples/streaming/gutenberg-stream-composition /zip-demo` |
| 2. JSONL records | `JsonlReader.records()` | `examples/streaming/gutenberg-stream-composition /events` |
| 3. Batching | `aiter_batches(records, size=...)` | `examples/streaming/gutenberg-stream-composition /demo`, `/pipeline/ingest-r2-lines` |
| 4. Stream-to-D1 style sink | `DemoD1Sink.insert_batch()` + checkpoints; real D1 line batches and `stream_checkpoints` rows | `examples/streaming/gutenberg-stream-composition /demo`, `/pipeline/ingest-r2-lines` |
| 5. Agent streaming | `DemoAgentSession.stream() -> AgentEvent` | `examples/streaming/gutenberg-stream-composition /events` |
| 6. AI/gateway token streaming | `DemoAIService.stream_text()` | `examples/streaming/gutenberg-stream-composition /events` |
| 7. WebSocket session stream | `DemoWebSocketSession.__aiter__()` | `examples/streaming/gutenberg-stream-composition /events` |
| 8. Resumable checkpoints | `Checkpoint` | `examples/streaming/gutenberg-stream-composition /demo` |

## Stream-to-stream target

```python
byte_stream = ByteStream(r2.object(key).iter_bytes())
records = JsonlReader(byte_stream.iter_lines()).records()

async for batch in aiter_batches(records, size=500):
    await db.insert_batch(batch)
    await progress.checkpoint(batch)
```

The current executable proof is `examples/streaming/gutenberg-stream-composition`, which uses Project Gutenberg's Shakespeare archive as the golden large-file source. `/zip-demo` reads this object through the R2 object's JavaScript `ReadableStream`, converts chunks at the FFI boundary, and opens the streamed ZIP bytes with Python `zipfile`. `/pipeline/ingest-r2-lines` then feeds extracted text lines into D1 in checkpointed batches, while `/fts/ingest` indexes text chunks into D1 FTS:

```text
r2://xampler-datasets/gutenberg/100/raw/pg100-h.zip
```

## ZIP caveat

ZIP central directories live at the end of the archive, so Python's standard `zipfile` API still needs a seekable byte buffer before entry extraction. Xampler now verifies direct R2 object-body streaming into that buffer; a fully non-seekable archive stream would require a different parser or an archive format designed for forward-only reads.

## Next integration work

The streaming types are now shared in `xampler.streaming` and used by the Gutenberg and HVSC examples. The next refactor should expand them into R2, Agents, AI Gateway, Workers AI, WebSockets, D1, Queues, Vectorize, and Workflows where the abstraction has proven value.
