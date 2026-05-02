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
5. `AgentSession.stream()` for typed agent events.
6. `AIService.stream_text()` / gateway-style text chunks.
7. WebSocket `async for` session shape.
8. `StreamCheckpoint` for resumable progress.

Run:

```bash
uv run pywrangler dev
uv run python ../scripts/verify_examples.py examples/streaming/gutenberg-stream-composition
```

Endpoints:

- `/golden` verifies the R2 golden file metadata.
- `/demo` runs a stream-to-stream local pipeline.
- `/events` returns typed AI/agent/WebSocket stream events.
