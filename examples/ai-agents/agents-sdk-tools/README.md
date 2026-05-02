# Agents 26 — Agents SDK shape from Python Workers

A Pythonic Cloudflare Agents SDK example.

Cloudflare Agents are stateful Workers applications that combine durable state, tools, model calls, and request/session routing. This example mirrors that API shape in Python Workers:

- `AgentMessage`, `AgentToolCall`, and `AgentRunResult` are typed dataclasses.
- `WeatherTool` is a deterministic tool for local verification.
- `DemoAgent` is the local/test transport.
- `AgentDurableObject` shows where durable per-agent session state belongs.
- `.raw` is kept on the session wrapper for future direct Agents SDK/DO interop.

Run locally:

```bash
uv run pywrangler dev
uv run python ../scripts/verify_examples.py examples/ai-agents/agents-sdk-tools
```

Try:

```bash
curl http://127.0.0.1:8787/demo?message=weather%20in%20Lagos
curl -X POST http://127.0.0.1:8787/agents/demo/run -d '{"message":"weather in Lagos"}'
```
