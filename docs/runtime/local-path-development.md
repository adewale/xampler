# Maintainer local-path development

Normal examples depend on the GitHub copy of Xampler:

```toml
"xampler @ git+https://github.com/adewale/xampler@main"
```

That is good for users, but annoying when a maintainer edits `xampler/` and an
example together before pushing. Use the local-path helper to build a local
wheel and point examples at that wheel temporarily:

```bash
uv run python scripts/use_local_xampler.py
uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage
uv run python scripts/verify_examples.py examples/streaming/gutenberg-stream-composition
```

Restore before committing:

```bash
uv run python scripts/use_local_xampler.py --restore
git diff -- examples/**/pyproject.toml
```

The helper only rewrites example `pyproject.toml` files that already depend on
`xampler`. It does not change `cfboundary` dependencies and it does not edit the
root package. Re-run the helper after editing `xampler/` so the wheel in `dist/`
reflects your changes; `dist/` is ignored by Git.
