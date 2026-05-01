# HVSC 24 — AI/Data Search Pipeline

An end-to-end Python Workers example using real release metadata from the High Voltage SID Collection downloads API:

- source data: `https://www.hvsc.c64.org/api/v1/version/7z`
- R2 stores the raw release document;
- D1 stores searchable release metadata;
- Queues model asynchronous ingestion;
- Workers AI is represented by a typed summarizer interface;
- Vectorize is represented by a typed deterministic local index for verifier realism;
- the HTTP API exposes ingest and search routes.

The verified local flow uses deterministic AI/vector substitutes because Workers AI and Vectorize require remote Cloudflare resources in local development. The real binding seams remain explicit in the code.

```bash
uv run python ../scripts/verify_examples.py hvsc-24-ai-data-search
```
