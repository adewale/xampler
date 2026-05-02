# Internal Consistency Audit

Last reviewed: 2026-05-02.

## Scope

This audit checks consistency after the breaking reorganization into `examples/<journey>/<example>/`.

## Checks performed

| Check | Result |
|---|---|
| Every example has expected project files | Pass |
| `pyproject.toml` names match folder paths | Pass |
| `wrangler.jsonc` Worker names match folder paths | Pass |
| `package.json` names are valid npm-style names, no raw slashes | Pass |
| Relative Markdown links resolve | Pass |
| Old numbered/example folder names remain in docs/scripts/tests | Pass: none found |
| `scripts/verify_examples.py --list` works with new names | Pass |
| `ruff`, `pyright`, `pytest` | Pass |
| Sample verification after reorg | Pass for hello, R2, streaming, and service-bindings provider |

## Fixes made during audit

- Normalized all `package.json` names from path-like names such as `xampler-examples/start/hello-worker` to package-safe names such as `xampler-start-hello-worker`.
- Fixed the Service Bindings verifier key to use the actual path: `examples/network-edge/service-bindings-rpc/py`.
- Fixed the TypeScript Service Binding service name to match the Python provider Worker name: `xampler-network-edge-service-bindings-rpc-py`.
- Rechecked README and docs for stale old folder names.

## Current top-level structure

```text
docs/
examples/
  start/
  storage-data/
  state-events/
  ai-agents/
  network-edge/
  streaming/
  full-apps/
scripts/
tests/
xampler/
```

## Remaining consistency concerns

| Concern | Recommendation |
|---|---|
| Some docs are now accurate but verbose. | Add a shorter `docs/index.md` or README doc map. |
| Service Bindings still has nested `py/` and `ts/`. | Keep for now; it is genuinely a multi-worker example. |
| Shared wrappers are still mostly per-example. | Gradually lift stable pieces into `xampler/` only after examples prove the API shape. |
| Verification names are now paths, which are explicit but long. | Optionally add short aliases later, but keep path names as canonical. |
```
