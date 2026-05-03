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

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
