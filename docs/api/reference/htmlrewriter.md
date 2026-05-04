# HTMLRewriter

Experimental surface: currently metadata types plus a deterministic transform helper, not a Python-native HTMLRewriter binding wrapper.

## Import

```python
from xampler.experimental.htmlrewriter import OpenGraphPage, OpenGraphRewriter
```

## Copy this API

```python
page = OpenGraphPage("Python Workers", "HTML rewritten at the edge")
html = OpenGraphRewriter(page).transform("<html><head></head><body>Hello</body></html>")
```

## Testability

Use local HTML fixture strings and assert inserted metadata before adding runtime-specific HTMLRewriter callbacks.
