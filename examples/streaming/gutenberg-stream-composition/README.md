# Streaming 27 — Gutenberg stream composition

A complicated streaming example built around Project Gutenberg's complete Shakespeare archive:

- source: <https://www.gutenberg.org/cache/epub/100/pg100-h.zip>
- R2 golden key: `gutenberg/100/raw/pg100-h.zip`
- bucket: `xampler-datasets`

It demonstrates the streaming API shape Xampler wants across primitives:

1. `iter_bytes()` / `iter_text()` / `iter_lines()` for object-like sources.
2. `JsonlReader.records()` for record streams.
3. `aiter_batches()` for backpressure-friendly batches.
4. Stream-to-D1 style batch sinks with checkpoints.
5. R2 ZIP extraction into a checkpointed D1 line-ingestion pipeline.
6. R2 ZIP extraction into D1 FTS5 full-text search.
7. `AgentSession.stream()` for typed agent events.
8. `AIService.stream_text()` / gateway-style text chunks.
9. WebSocket `async for` session shape.
10. `Checkpoint` for resumable progress.

Run:

```bash
uv run pywrangler dev
uv run python ../scripts/verify_examples.py examples/streaming/gutenberg-stream-composition
```

Endpoints:

- `/golden` verifies the R2 golden file metadata.
- `/demo` runs a stream-to-stream local pipeline.
- `/events` returns typed AI/agent/WebSocket stream events.
- `/zip-demo` reads `gutenberg/100/raw/pg100-h.zip` through the R2 object `ReadableStream`, then opens the streamed bytes with `zipfile` and reads the first HTML entry. In local Wrangler mode, the endpoint seeds the local R2 bucket from the Gutenberg source URL if the golden object is missing; deployed/remote runs use the existing `xampler-datasets` object directly.
- `/pipeline/ingest-r2-lines` extracts the full Shakespeare HTML entry, turns it into text lines, writes those lines to D1 in batches, and updates a `stream_checkpoints` row after every batch.
- `/pipeline/status` returns the D1 line count and checkpoint state.
- `/fts/ingest` extracts the full Shakespeare HTML entry, strips tags, chunks all text, writes every chunk into D1, and mirrors it into a D1 FTS5 virtual table.
- `/fts/search?q=romeo%20juliet` runs a full-text query over the indexed chunks.
- `/fts/verify` checks chunk count equals FTS row count and runs several Shakespeare queries (`romeo juliet`, `hamlet`, `tempest`, etc.) to prove the archive was indexed.

## Cloudflare docs

- [R2](https://developers.cloudflare.com/r2/)
- [ReadableStream](https://developers.cloudflare.com/workers/runtime-apis/streams/)
