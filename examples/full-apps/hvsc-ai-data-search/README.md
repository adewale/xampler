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

Run an interactive browser session from the repository root:

```bash
uv run python scripts/serve_hvsc.py
```

Then open <http://localhost:9595/>.

For arbitrary composer/title/path search, first build and import the real catalog from the archive:

```bash
uv run python scripts/hvsc_full_pipeline.py --skip-upload
```

If you want to upload the raw archive and catalog to your permanent R2 bucket too:

```bash
uv run python scripts/hvsc_full_pipeline.py --bucket xampler-datasets
```

Then use the numbered buttons in the page:

1. Verify the full archive object in R2.
2. Ingest release metadata.
3. Verify a generated `tracks.jsonl` catalog object in R2.
4. Import all catalog shards from R2 into D1 while the browser shows progress.
5. Search the D1 catalog for arbitrary terms such as `jeroen`, `maniacs`, `hubbard`, or any composer/file present in the imported catalog.

You can also open <http://localhost:9595/search?q=sid> or <http://localhost:9595/tracks?q=jeroen>.

The page also has an optional button to stream the full HVSC archive into local R2:

- source: `https://boswme.home.xs4all.nl/HVSC/HVSC_84-all-of-them.7z`
- size: `83,748,140` bytes, about `79.9 MiB`
- R2 key: `hvsc/84/raw/HVSC_84-all-of-them.7z`

This large archive is intentionally **not** part of the default verifier. Use it for interactive stress testing of streaming R2 writes.

To build a real catalog from the full archive, see [`docs/data/datasets.md`](../../../docs/data/datasets.md):

```bash
uv run python scripts/hvsc_download_unpack.py
uv run python scripts/hvsc_build_catalog.py --shard-size 500
uv run python scripts/hvsc_upload_archive.py xampler-datasets
uv run python scripts/hvsc_upload_catalog.py xampler-datasets
```

The upload scripts target remote Cloudflare R2 by default. Add `--local` only when you intentionally want to seed Wrangler's local R2 store.

Run the automated verifier:

```bash
uv run python scripts/verify_examples.py examples/full-apps/hvsc-ai-data-search
```
