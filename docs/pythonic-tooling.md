# Pythonic Tooling Policy

Last reviewed: 2026-05-01.

The examples should be runnable by Python developers without first learning an npm workflow.

## Default commands

Use `uv` and `pywrangler` for Python Worker examples:

```bash
uv run pywrangler dev
uv run pywrangler deploy
uv run python scripts/verify_examples.py r2-01
```

Do **not** require this for Python examples:

```bash
npm install
npm run dev
```

## Why Node still appears

Wrangler is implemented in JavaScript. `pywrangler` currently delegates to Wrangler internally, and its logs may show `npx wrangler ...`. That is acceptable as an implementation detail.

The user-facing workflow should still be Pythonic:

- `uv` creates the Python environment;
- `pywrangler` vendors Python dependencies into `python_modules`;
- `scripts/verify_examples.py` starts Workers and performs smoke checks.

## Exceptions

Some Cloudflare surfaces are not Python Worker surfaces:

- `pages-23-functions` uses Pages Functions, which are JavaScript/TypeScript today.
- `service-bindings-13-rpc/ts` intentionally includes a TypeScript client to demonstrate cross-language RPC.

For those examples, Node/Wrangler commands are allowed, but they should be isolated and documented as exceptions.
