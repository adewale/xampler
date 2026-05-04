# Browser Rendering 18 — Screenshot

Uses the Browser Rendering REST API from a Python Worker. The real route supports screenshot smoke checks plus deeper `/content`, `/pdf`, and `/scrape` checks against `https://example.com`. The local `/report` and `/demo/report-verifier` routes provide deterministic report/content/PDF/screenshot assertions.

Local `/demo` verification is deterministic. For real remote verification, run the prepared deployed flow; the prepare script infers `ACCOUNT_ID` from `wrangler whoami`, stores `ACCOUNT_ID` and `CF_API_TOKEN` as Worker secrets, deploys the Worker, and records the deployed URL.

```bash
npx --yes wrangler login
CLOUDFLARE_API_TOKEN=... \
XAMPLER_RUN_REMOTE=1 XAMPLER_PREPARE_REMOTE=1 \
  uv run python scripts/prepare_remote_examples.py browser-rendering
XAMPLER_RUN_REMOTE=1 XAMPLER_REMOTE_BROWSER_RENDERING=1 \
  uv run python scripts/verify_remote_examples.py browser-rendering
```

## Cloudflare docs

- [Browser Rendering](https://developers.cloudflare.com/browser-rendering/)

## Copy this API

```python
from xampler.browser_rendering import BrowserRendering, ScreenshotRequest

browser = BrowserRendering(account_id, token)
response = await browser.screenshot(ScreenshotRequest(url="https://example.com"))
```
