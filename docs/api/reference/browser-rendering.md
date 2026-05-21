# Browser Rendering

## Import

```python
from xampler.browser_rendering import BrowserRendering, ScreenshotRequest
```

## Copy this API

```python
browser = BrowserRendering(account_id, token)
response = await browser.screenshot(ScreenshotRequest(url="https://example.com"))
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Demo screenshot metadata | Demo-only | Local tests validate typed request/result shape. |
| Screenshot/content/PDF/scrape REST calls | Remote-only | Requires account/token and Browser Rendering product access. |
| Browser binding/Puppeteer control | Not covered | REST wrapper only today. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
