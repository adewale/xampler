# HTMLRewriter

## Import

```python
from xampler.htmlrewriter import OpenGraphPage, OpenGraphRewriter
```

## Copy this API

```python
page = OpenGraphPage("Python Workers", "HTML rewritten at the edge")
html = OpenGraphRewriter(page).transform("<html><head></head><body>Hello</body></html>")
```

## Testability

Use local HTML fixture strings and assert inserted metadata before adding runtime-specific HTMLRewriter callbacks.
